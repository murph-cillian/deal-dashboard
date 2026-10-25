"""SQLAlchemy playground: Person and Pet.

A scratch file for learning. Keep it OUTSIDE your repo (or in a gitignored
folder). Run with:  uv run python sqlalchemy_playground.py

echo=True makes SQLAlchemy print every SQL statement it runs. Read that output
alongside the code: it is how you learn what each line really does.
"""

from sqlalchemy import ForeignKey, create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


# --------------------------------------------------------------------------
# Step 1: declare the tables as classes
# --------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Parent of every table class. Holds the catalogue in Base.metadata."""


class Person(Base):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]  # NOT NULL, because the type has no "| None"
    age: Mapped[int | None]  # nullable, because of "| None"

    # Python-level convenience: person.pets is a list of Pet objects.
    pets: Mapped[list["Pet"]] = relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"Person(id={self.id}, name={self.name!r}, age={self.age})"


class Pet(Base):
    __tablename__ = "pet"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    # Database-level link: this column must hold an existing person.id.
    owner_id: Mapped[int] = mapped_column(ForeignKey("person.id"))

    owner: Mapped["Person"] = relationship(back_populates="pets")

    def __repr__(self) -> str:
        return f"Pet(id={self.id}, name={self.name!r}, owner_id={self.owner_id})"


def banner(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def main() -> None:
    # ----------------------------------------------------------------------
    # Step 2: create an in-memory engine. "sqlite://" with nothing after it
    # means a throwaway database that vanishes when the program ends.
    # ----------------------------------------------------------------------
    engine = create_engine("sqlite://", echo=True)

    # ----------------------------------------------------------------------
    # Step 3: create the tables from the classes. Read the CREATE TABLE
    # statements in the output: they come straight from your type hints.
    # ----------------------------------------------------------------------
    banner("STEP 3: create_all (watch the CREATE TABLE statements)")
    Base.metadata.create_all(engine)

    # ----------------------------------------------------------------------
    # Step 4: add people. Nothing is sent to the database until flush/commit.
    # ----------------------------------------------------------------------
    banner("STEP 4: add three people and commit")
    with Session(engine) as session:
        session.add_all(
            [
                Person(name="Alice", age=30),
                Person(name="Bob", age=25),
                Person(name="Cara", age=None),  # age is nullable
            ]
        )
        # Note: no INSERT has been printed yet. The session is only holding them.
        print(">>> about to commit: the INSERTs are sent now")
        session.commit()

    # ----------------------------------------------------------------------
    # Step 4b: query them back with select().where()
    # ----------------------------------------------------------------------
    banner("STEP 4b: query people older than 26")
    with Session(engine) as session:
        stmt = select(Person).where(Person.age > 26)
        print(">>> the statement object prints as SQL:\n", stmt)
        older = session.scalars(stmt).all()
        print(">>> result:", older)

    # ----------------------------------------------------------------------
    # Step 5: change an attribute and commit. You never write UPDATE: the
    # session notices the change (unit of work) and emits it for you.
    # ----------------------------------------------------------------------
    banner("STEP 5: change Bob's age (watch for the UPDATE)")
    with Session(engine) as session:
        bob = session.scalars(select(Person).where(Person.name == "Bob")).one()
        bob.age = 26  # plain Python assignment
        print(">>> assigned, but no UPDATE yet")
        session.commit()

    # ----------------------------------------------------------------------
    # Identity map demo: loading the same row twice gives the SAME object.
    # ----------------------------------------------------------------------
    banner("IDENTITY MAP: get the same row twice")
    with Session(engine) as session:
        a = session.get(Person, 1)
        b = session.get(Person, 1)  # no second SELECT: served from the identity map
        print(">>> a is b:", a is b)

    # ----------------------------------------------------------------------
    # Step 6: pets through the relationship. We never touch owner_id by
    # hand: appending to person.pets sets it when the session flushes.
    # ----------------------------------------------------------------------
    banner("STEP 6: add pets via the relationship")
    with Session(engine) as session:
        alice = session.scalars(select(Person).where(Person.name == "Alice")).one()
        alice.pets.append(Pet(name="Rex"))
        alice.pets.append(Pet(name="Misty"))
        session.commit()

    with Session(engine) as session:
        alice = session.scalars(select(Person).where(Person.name == "Alice")).one()
        print(">>> alice.pets:", alice.pets)  # triggers a SELECT on first access
        rex = session.scalars(select(Pet).where(Pet.name == "Rex")).one()
        print(">>> rex.owner:", rex.owner)  # follows the foreign key back

    # ----------------------------------------------------------------------
    # flush vs commit vs rollback
    # ----------------------------------------------------------------------
    banner("FLUSH vs COMMIT vs ROLLBACK")
    with Session(engine) as session:
        dan = Person(name="Dan", age=40)
        session.add(dan)
        print(">>> before flush, dan.id =", dan.id)  # None: DB has not assigned it
        session.flush()
        print(">>> after flush,  dan.id =", dan.id)  # assigned, still inside the transaction
        session.rollback()  # throw it away
    with Session(engine) as session:
        names = session.scalars(select(Person.name)).all()
        print(">>> people in DB after rollback:", names, "(no Dan)")

    # ----------------------------------------------------------------------
    # The idiom used in the real project: begin() as a context manager.
    # Commit if the block finishes, roll back if an exception escapes.
    # ----------------------------------------------------------------------
    banner("session.begin(): automatic commit / rollback")
    try:
        with Session(engine) as session, session.begin():
            session.add(Person(name="Eve", age=22))
            raise RuntimeError("simulated crash halfway through")
    except RuntimeError as exc:
        print(">>> caught:", exc)
    with Session(engine) as session:
        print(">>> people after the crash:", session.scalars(select(Person.name)).all(), "(no Eve)")

    engine.dispose()

    # ----------------------------------------------------------------------
    # Step 7: break it deliberately. SQLite ignores foreign keys by default.
    # ----------------------------------------------------------------------
    banner("STEP 7a: orphan pet, foreign keys NOT enforced (SQLite default)")
    quiet = create_engine("sqlite://")  # no echo, to keep the output readable
    Base.metadata.create_all(quiet)
    with Session(quiet) as session:
        session.add(Pet(name="Ghost", owner_id=999))  # person 999 does not exist!
        session.commit()
        print(">>> committed an orphan pet. Nothing complained. That is the danger.")
    quiet.dispose()

    banner("STEP 7b: same thing with PRAGMA foreign_keys=ON")
    strict = create_engine("sqlite://")

    @event.listens_for(strict, "connect")
    def _enable_fk(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN001
        dbapi_connection.execute("PRAGMA foreign_keys=ON")  # type: ignore[no-untyped-call]  # noqa: ANN201

    Base.metadata.create_all(strict)
    with Session(strict) as session:
        session.add(Pet(name="Ghost", owner_id=999))
        try:
            session.commit()
        except IntegrityError as exc:
            print(">>> IntegrityError, as it should be:", exc.orig)
            session.rollback()
    strict.dispose()


if __name__ == "__main__":
    main()
