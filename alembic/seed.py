"""
Seed script for SAMi Backend Database
Seeds reference data: cinema types, movies, and cinemas
Schedules are generated through the forecast system
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models.movie import Movie
from app.models.cinema import Cinema, CinemaType
from app.models.schedule import Schedule
from app.models.chat import ChatSession, ChatMessage
from app.models.forecast import Forecast, PredictionData
from datetime import datetime
import uuid


def seed_database():
    """Seed database with cinema types, movies, and cinemas"""
    db = SessionLocal()

    try:
        print("Starting database seeding...")

        # Clear existing data (optional - be careful in production!)
        print("Clearing existing data...")
        db.query(PredictionData).delete()  # Delete prediction data first (foreign key dependency)
        db.query(Forecast).delete()  # Delete forecasts second
        db.query(Schedule).delete()  # Delete schedules third
        db.query(Cinema).delete()
        db.query(Movie).delete()
        db.query(CinemaType).delete()
        db.query(ChatMessage).delete()  # Clear chat messages
        db.query(ChatSession).delete()  # Clear chat sessions
        db.commit()

        # Seed cinema types
        print("Seeding cinema types...")
        cinema_types = [
            CinemaType(
                id="standard",
                name="Standard",
                description="Traditional cinema experience with comfortable seating",
                price_multiplier=1.0,
            ),
            CinemaType(
                id="premium",
                name="Premium",
                description="Enhanced experience with luxury seating and superior sound",
                price_multiplier=1.5,
            ),
            CinemaType(
                id="imax",
                name="IMAX",
                description="Large format screens with immersive sound technology",
                price_multiplier=2.0,
            ),
            CinemaType(
                id="vip",
                name="VIP",
                description="Exclusive experience with reclining seats and table service",
                price_multiplier=2.5,
            ),
        ]

        for cinema_type in cinema_types:
            db.add(cinema_type)
        db.commit()
        print(f"Seeded {len(cinema_types)} cinema types")

        # Seed expanded movies catalog (same 30 movies)
        print("Seeding expanded movie catalog...")
        movies = [
            # Recent blockbusters
            Movie(
                title="Guardians of the Galaxy Vol. 3",
                duration=150,
                genre="Action",
                rating="PG-13",
                description="Peter Quill, still reeling from the loss of Gamora, must rally his team around him to defend the universe along with protecting one of their own.",
                poster="https://image.tmdb.org/t/p/w500/r2J02Z2OpNTctfOSN1Ydgii51I3.jpg",
                release_date=datetime(2023, 5, 5),
            ),
            Movie(
                title="Spider-Man: Across the Spider-Verse",
                duration=140,
                genre="Animation",
                rating="PG",
                description="Miles Morales catapults across the Multiverse, where he encounters a team of Spider-People charged with protecting its very existence.",
                poster="https://image.tmdb.org/t/p/w500/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg",
                release_date=datetime(2023, 6, 2),
            ),
            Movie(
                title="The Little Mermaid",
                duration=135,
                genre="Fantasy",
                rating="PG",
                description="A young mermaid makes a deal with a sea witch to trade her beautiful voice for human legs so she can discover the world above water.",
                poster="https://image.tmdb.org/t/p/w500/ym1dxyOk4jFcSl4Q2zmRrA5BEEN.jpg",
                release_date=datetime(2023, 5, 26),
            ),
            Movie(
                title="Fast X",
                duration=141,
                genre="Action",
                rating="PG-13",
                description="Dom Toretto and his family are targeted by the vengeful son of drug kingpin Hernan Reyes.",
                poster="https://image.tmdb.org/t/p/w500/fiVW06jE7z9YnO4trhaMEdclSiC.jpg",
                release_date=datetime(2023, 5, 19),
            ),
            Movie(
                title="Indiana Jones and the Dial of Destiny",
                duration=154,
                genre="Adventure",
                rating="PG-13",
                description="Archaeologist Indiana Jones races against time to retrieve a legendary artifact that can change the course of history.",
                poster="https://image.tmdb.org/t/p/w500/Af4bXE63pVsb2FtbW8uYIyPBadD.jpg",
                release_date=datetime(2023, 6, 30),
            ),
            Movie(
                title="Oppenheimer",
                duration=180,
                genre="Drama",
                rating="R",
                description="The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.",
                poster="https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
                release_date=datetime(2023, 7, 21),
            ),
            Movie(
                title="Barbie",
                duration=114,
                genre="Comedy",
                rating="PG-13",
                description="Barbie and Ken are having the time of their lives in the colorful and seemingly perfect world of Barbie Land.",
                poster="https://image.tmdb.org/t/p/w500/iuFNMS8U5cb6xfzi51Dbkovj7vM.jpg",
                release_date=datetime(2023, 7, 21),
            ),
            Movie(
                title="Mission: Impossible – Dead Reckoning Part One",
                duration=163,
                genre="Action",
                rating="PG-13",
                description="Ethan Hunt and his IMF team embark on their most dangerous mission yet: to track down a terrifying new weapon.",
                poster="https://image.tmdb.org/t/p/w500/NNxYkU70HPurnNCSiCjYAmacwm.jpg",
                release_date=datetime(2023, 7, 12),
            ),
            Movie(
                title="Sound of Freedom",
                duration=131,
                genre="Drama",
                rating="PG-13",
                description="The story of Tim Ballard, a former US government agent, who quits his job in order to devote his life to rescuing children from global sex traffickers.",
                poster="https://image.tmdb.org/t/p/w500/qA5kPYZA7FkVvqcEfJRoOy4kpHg.jpg",
                release_date=datetime(2023, 7, 4),
            ),
            Movie(
                title="Transformers: Rise of the Beasts",
                duration=127,
                genre="Science Fiction",
                rating="PG-13",
                description="During the '90s, a new faction of Transformers - the Maximals - join the Autobots as allies in the battle for Earth.",
                poster="https://image.tmdb.org/t/p/w500/gPbM0MK8CP8A174rmUwGsADNYKD.jpg",
                release_date=datetime(2023, 6, 9),
            ),
            Movie(
                title="John Wick: Chapter 4",
                duration=169,
                genre="Action",
                rating="R",
                description="John Wick uncovers a path to defeating The High Table. But before he can earn his freedom, he must face off against a new enemy.",
                poster="https://image.tmdb.org/t/p/w500/vZloFAK7NmvMGKE7VkF5UHaz0I.jpg",
                release_date=datetime(2023, 3, 24),
            ),
            Movie(
                title="Avatar: The Way of Water",
                duration=192,
                genre="Science Fiction",
                rating="PG-13",
                description="Jake Sully lives with his newfound family formed on the extrasolar moon Pandora.",
                poster="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg",
                release_date=datetime(2022, 12, 16),
            ),
            Movie(
                title="Top Gun: Maverick",
                duration=131,
                genre="Action",
                rating="PG-13",
                description="After thirty years, Maverick is still pushing the envelope as a top naval aviator.",
                poster="https://image.tmdb.org/t/p/w500/62HCnUTziyWcpDaBO2i1DX17ljH.jpg",
                release_date=datetime(2022, 5, 27),
            ),
            Movie(
                title="The Batman",
                duration=176,
                genre="Crime",
                rating="PG-13",
                description="When a sadistic serial killer begins murdering key political figures in Gotham, Batman is forced to investigate the city's hidden corruption.",
                poster="https://image.tmdb.org/t/p/w500/74xTEgt7R36Fpooo50r9T25onhq.jpg",
                release_date=datetime(2022, 3, 4),
            ),
            Movie(
                title="Everything Everywhere All at Once",
                duration=139,
                genre="Comedy",
                rating="R",
                description="A middle-aged Chinese immigrant is swept up into an insane adventure in which she alone can save existence.",
                poster="https://image.tmdb.org/t/p/w500/u68AjlvlutfEIcpmbYpKcdi09ut.jpg",
                release_date=datetime(2022, 3, 25),
            ),
            Movie(
                title="Dune",
                duration=155,
                genre="Science Fiction",
                rating="PG-13",
                description="A noble family becomes embroiled in a war for control over the galaxy's most valuable asset.",
                poster="https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
                release_date=datetime(2021, 10, 22),
            ),
            Movie(
                title="No Time to Die",
                duration=163,
                genre="Action",
                rating="PG-13",
                description="James Bond has left active service. His peace is short-lived when Felix Leiter, an old friend from the CIA, turns up asking for help.",
                poster="https://image.tmdb.org/t/p/w500/iUgygt3fscRoKWCV1d0C7FbM9TP.jpg",
                release_date=datetime(2021, 10, 8),
            ),
            Movie(
                title="The French Dispatch",
                duration=107,
                genre="Comedy",
                rating="R",
                description="A love letter to journalists set in an outpost of an American newspaper in a fictional twentieth-century French city.",
                poster="https://image.tmdb.org/t/p/w500/audiWhmdSV5q6C6256PJe9gBs6R.jpg",
                release_date=datetime(2021, 10, 22),
            ),
            Movie(
                title="Encanto",
                duration=102,
                genre="Animation",
                rating="PG",
                description="A Colombian teenage girl has to face the frustration of being the only member of her family without magical powers.",
                poster="https://image.tmdb.org/t/p/w500/4j0PNHkMr5ax3IA8tjtxcmPU3QT.jpg",
                release_date=datetime(2021, 11, 24),
            ),
            Movie(
                title="The Power of the Dog",
                duration=128,
                genre="Drama",
                rating="R",
                description="A domineering rancher responds with mocking cruelty when his brother brings home a new wife and her son.",
                poster="https://image.tmdb.org/t/p/w500/ltvP3B23X7tvYnJd3awhxSgkg4U.jpg",
                release_date=datetime(2021, 12, 1),
            ),
            Movie(
                title="Don't Look Up",
                duration=138,
                genre="Comedy",
                rating="R",
                description="Two low-level astronomers must go on a giant media tour to warn mankind of an approaching comet that will destroy planet Earth.",
                poster="https://image.tmdb.org/t/p/w500/th4E1yqsE8DGpAseLiUrI60Hf8V.jpg",
                release_date=datetime(2021, 12, 24),
            ),
            Movie(
                title="West Side Story",
                duration=156,
                genre="Musical",
                rating="PG-13",
                description="An adaptation of the 1957 musical, West Side Story explores forbidden love and the rivalry between the Jets and the Sharks.",
                poster="https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg",
                release_date=datetime(2021, 12, 10),
            ),
            Movie(
                title="The Matrix Resurrections",
                duration=148,
                genre="Science Fiction",
                rating="R",
                description="Return to a world of two realities: one, everyday life; the other, what lies behind it.",
                poster="https://image.tmdb.org/t/p/w500/8c4a8kE7PizaGQQnditMmI1xbRp.jpg",
                release_date=datetime(2021, 12, 22),
            ),
            Movie(
                title="Black Widow",
                duration=134,
                genre="Action",
                rating="PG-13",
                description="Natasha Romanoff confronts the darker parts of her ledger when a dangerous conspiracy with ties to her past arises.",
                poster="https://image.tmdb.org/t/p/w500/7JPpIjhD2V0sKyFvhB9khUMa30d.jpg",
                release_date=datetime(2021, 7, 9),
            ),
            Movie(
                title="Shang-Chi and the Legend of the Ten Rings",
                duration=132,
                genre="Action",
                rating="PG-13",
                description="Shang-Chi must confront the past he thought he left behind when he is drawn into the web of the mysterious Ten Rings organization.",
                poster="https://image.tmdb.org/t/p/w500/d08HqqeBQSwN8i8MEvpsZ8Cb438.jpg",
                release_date=datetime(2021, 9, 3),
            ),
            Movie(
                title="A Quiet Place Part II",
                duration=97,
                genre="Horror",
                rating="PG-13",
                description="Following the events at home, the Abbott family now face the terrors of the outside world.",
                poster="https://image.tmdb.org/t/p/w500/bShgiEQoPnWdw4LBrYT5u18JF34.jpg",
                release_date=datetime(2021, 5, 28),
            ),
            Movie(
                title="The Conjuring: The Devil Made Me Do It",
                duration=112,
                genre="Horror",
                rating="R",
                description="The Warrens investigate a murder that may be linked to a demonic possession.",
                poster="https://image.tmdb.org/t/p/w500/4q2hz2m8hubgvijz8Ez0T2Os2Yv.jpg",
                release_date=datetime(2021, 6, 4),
            ),
            Movie(
                title="Scream",
                duration=114,
                genre="Horror",
                rating="R",
                description="Twenty-five years after a streak of brutal murders shocked the quiet town of Woodsboro, a new killer has donned the Ghostface mask.",
                poster="https://image.tmdb.org/t/p/w500/xEt2GSz9z5rSVpIHMiGdtf0czyf.jpg",
                release_date=datetime(2022, 1, 14),
            ),
            Movie(
                title="Turning Red",
                duration=100,
                genre="Animation",
                rating="PG",
                description="A thirteen-year-old girl named Mei Lee is torn between staying her mother's dutiful daughter and the changes of adolescence.",
                poster="https://image.tmdb.org/t/p/w500/qsdjk9oAKSQMWs0Vt5Pyfh6O4GZ.jpg",
                release_date=datetime(2022, 3, 11),
            ),
            Movie(
                title="Luca",
                duration=95,
                genre="Animation",
                rating="PG",
                description="On the Italian Riviera, an unlikely but strong friendship grows between a human being and a sea monster disguised as a human.",
                poster="https://image.tmdb.org/t/p/w500/pEz5aROvfy5FBW1OTlrDO3VryWO.jpg",
                release_date=datetime(2021, 6, 18),
            ),
        ]

        for movie in movies:
            db.add(movie)
        db.commit()
        print(f"Seeded {len(movies)} movies")

        # Seed cinemas (same 20 cinemas)
        print("Seeding cinemas...")
        cinemas = [
            Cinema(
                number=1,
                type="standard",
                total_seats=120,
                location="Ground Floor - East Wing",
                features=["Digital Sound", "Stadium Seating"],
            ),
            Cinema(
                number=2,
                type="standard",
                total_seats=150,
                location="Ground Floor - West Wing",
                features=["Digital Sound", "Stadium Seating"],
            ),
            Cinema(
                number=3,
                type="premium",
                total_seats=100,
                location="Second Floor - North",
                features=["Dolby Atmos", "Leather Recliners", "Cup Holders"],
            ),
            Cinema(
                number=4,
                type="standard",
                total_seats=180,
                location="Ground Floor - Center",
                features=["Digital Sound", "Stadium Seating"],
            ),
            Cinema(
                number=5,
                type="premium",
                total_seats=90,
                location="Second Floor - South",
                features=["Dolby Atmos", "Luxury Seating", "Extra Legroom"],
            ),
            Cinema(
                number=6,
                type="imax",
                total_seats=300,
                location="Third Floor - IMAX Theater",
                features=["IMAX Screen", "IMAX Sound System", "Reserved Seating"],
            ),
            Cinema(
                number=7,
                type="standard",
                total_seats=140,
                location="Ground Floor - South Wing",
                features=["Digital Sound", "Stadium Seating"],
            ),
            Cinema(
                number=8,
                type="vip",
                total_seats=50,
                location="Fourth Floor - VIP Lounge",
                features=[
                    "Reclining Seats",
                    "Table Service",
                    "Premium Bar",
                    "Gourmet Menu",
                ],
            ),
            Cinema(
                number=9,
                type="standard",
                total_seats=160,
                location="Second Floor - East",
                features=["Digital Sound", "Stadium Seating"],
            ),
            Cinema(
                number=10,
                type="premium",
                total_seats=110,
                location="Second Floor - West",
                features=["Dolby Digital", "Luxury Seating", "Wide Screens"],
            ),
            Cinema(
                number=11,
                type="standard",
                total_seats=200,
                location="Ground Floor - Main Hall",
                features=["Digital Sound", "Stadium Seating", "Large Screen"],
            ),
            Cinema(
                number=12,
                type="standard",
                total_seats=130,
                location="Second Floor - Center",
                features=["Digital Sound", "Stadium Seating"],
            ),
            Cinema(
                number=13,
                type="premium",
                total_seats=80,
                location="Third Floor - Premium Suite",
                features=["THX Certified", "Heated Seats", "Premium Sound"],
            ),
            Cinema(
                number=14,
                type="standard",
                total_seats=170,
                location="Ground Floor - North Wing",
                features=["Digital Sound", "Stadium Seating"],
            ),
            Cinema(
                number=15,
                type="imax",
                total_seats=280,
                location="Third Floor - IMAX Dome",
                features=["IMAX Dome", "Immersive Sound", "Reserved Seating"],
            ),
            Cinema(
                number=16,
                type="standard",
                total_seats=145,
                location="Second Floor - Corner",
                features=["Digital Sound", "Stadium Seating"],
            ),
            Cinema(
                number=17,
                type="vip",
                total_seats=60,
                location="Fourth Floor - Executive",
                features=["Massage Chairs", "Personal Service", "Premium Concessions"],
            ),
            Cinema(
                number=18,
                type="premium",
                total_seats=95,
                location="Third Floor - East",
                features=["Dolby Vision", "Reclining Seats", "Enhanced Sound"],
            ),
            Cinema(
                number=19,
                type="standard",
                total_seats=155,
                location="Ground Floor - Corner",
                features=["Digital Sound", "Stadium Seating"],
            ),
            Cinema(
                number=20,
                type="premium",
                total_seats=105,
                location="Third Floor - West",
                features=["4DX Technology", "Motion Seats", "Environmental Effects"],
            ),
        ]

        for cinema in cinemas:
            db.add(cinema)
        db.commit()
        print(f"Seeded {len(cinemas)} cinemas")

        print("Database seeding completed successfully!")
        print("Summary:")
        print(f"   - Cinema Types: {len(cinema_types)}")
        print(f"   - Movies: {len(movies)}")
        print(f"   - Cinemas: {len(cinemas)}")
        print("\nSchedules will be generated through the forecast system.")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
