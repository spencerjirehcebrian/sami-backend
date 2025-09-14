"""
Seed script for SAMi Backend Database
Converts frontend mock data to backend database format
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.movie import Movie
from app.models.cinema import Cinema, CinemaType
from app.models.schedule import Schedule
from datetime import datetime
import uuid


def seed_database():
    """Seed database with cinema types, movies, and cinemas from frontend mock data"""
    db = SessionLocal()

    try:
        print("🌱 Starting database seeding...")

        # Clear existing data (optional - be careful in production!)
        print("🧹 Clearing existing data...")
        db.query(Schedule).delete()
        db.query(Cinema).delete()
        db.query(Movie).delete()
        db.query(CinemaType).delete()
        db.commit()

        # Seed cinema types
        print("🎭 Seeding cinema types...")
        cinema_types = [
            CinemaType(
                id="standard",
                name="Standard",
                description="Traditional cinema experience with comfortable seating",
                price_multiplier=1.0
            ),
            CinemaType(
                id="premium",
                name="Premium",
                description="Enhanced experience with luxury seating and superior sound",
                price_multiplier=1.5
            ),
            CinemaType(
                id="imax",
                name="IMAX",
                description="Large format screens with immersive sound technology",
                price_multiplier=2.0
            ),
            CinemaType(
                id="vip",
                name="VIP",
                description="Exclusive experience with reclining seats and table service",
                price_multiplier=2.5
            ),
        ]

        for cinema_type in cinema_types:
            db.add(cinema_type)
        db.commit()
        print(f"✅ Seeded {len(cinema_types)} cinema types")

        # Seed movies
        print("🎬 Seeding movies...")
        movies = [
            Movie(
                title="Guardians of the Galaxy Vol. 3",
                duration=150,
                genre="Action",
                rating="PG-13",
                description="Peter Quill, still reeling from the loss of Gamora, must rally his team around him to defend the universe along with protecting one of their own.",
                release_date=datetime(2023, 5, 5)
            ),
            Movie(
                title="Spider-Man: Across the Spider-Verse",
                duration=140,
                genre="Animation",
                rating="PG",
                description="Miles Morales catapults across the Multiverse, where he encounters a team of Spider-People charged with protecting its very existence.",
                release_date=datetime(2023, 6, 2)
            ),
            Movie(
                title="The Little Mermaid",
                duration=135,
                genre="Fantasy",
                rating="PG",
                description="A young mermaid makes a deal with a sea witch to trade her beautiful voice for human legs so she can discover the world above water.",
                release_date=datetime(2023, 5, 26)
            ),
            Movie(
                title="Fast X",
                duration=141,
                genre="Action",
                rating="PG-13",
                description="Dom Toretto and his family are targeted by the vengeful son of drug kingpin Hernan Reyes.",
                release_date=datetime(2023, 5, 19)
            ),
            Movie(
                title="Indiana Jones and the Dial of Destiny",
                duration=154,
                genre="Adventure",
                rating="PG-13",
                description="Archaeologist Indiana Jones races against time to retrieve a legendary artifact that can change the course of history.",
                release_date=datetime(2023, 6, 30)
            ),
            Movie(
                title="Oppenheimer",
                duration=180,
                genre="Drama",
                rating="R",
                description="The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.",
                release_date=datetime(2023, 7, 21)
            ),
            Movie(
                title="Barbie",
                duration=114,
                genre="Comedy",
                rating="PG-13",
                description="Barbie and Ken are having the time of their lives in the colorful and seemingly perfect world of Barbie Land.",
                release_date=datetime(2023, 7, 21)
            ),
            Movie(
                title="Mission: Impossible – Dead Reckoning Part One",
                duration=163,
                genre="Action",
                rating="PG-13",
                description="Ethan Hunt and his IMF team embark on their most dangerous mission yet: to track down a terrifying new weapon.",
                release_date=datetime(2023, 7, 12)
            ),
            Movie(
                title="Sound of Freedom",
                duration=131,
                genre="Drama",
                rating="PG-13",
                description="The story of Tim Ballard, a former US government agent, who quits his job in order to devote his life to rescuing children from global sex traffickers.",
                release_date=datetime(2023, 7, 4)
            ),
            Movie(
                title="Transformers: Rise of the Beasts",
                duration=127,
                genre="Science Fiction",
                rating="PG-13",
                description="During the '90s, a new faction of Transformers - the Maximals - join the Autobots as allies in the battle for Earth.",
                release_date=datetime(2023, 6, 9)
            ),
            Movie(
                title="John Wick: Chapter 4",
                duration=169,
                genre="Action",
                rating="R",
                description="John Wick uncovers a path to defeating The High Table. But before he can earn his freedom, he must face off against a new enemy.",
                release_date=datetime(2023, 3, 24)
            ),
            Movie(
                title="Avatar: The Way of Water",
                duration=192,
                genre="Science Fiction",
                rating="PG-13",
                description="Jake Sully lives with his newfound family formed on the extrasolar moon Pandora.",
                release_date=datetime(2022, 12, 16)
            ),
            Movie(
                title="Top Gun: Maverick",
                duration=131,
                genre="Action",
                rating="PG-13",
                description="After thirty years, Maverick is still pushing the envelope as a top naval aviator.",
                release_date=datetime(2022, 5, 27)
            ),
            Movie(
                title="The Batman",
                duration=176,
                genre="Crime",
                rating="PG-13",
                description="When a sadistic serial killer begins murdering key political figures in Gotham, Batman is forced to investigate the city's hidden corruption.",
                release_date=datetime(2022, 3, 4)
            ),
            Movie(
                title="Everything Everywhere All at Once",
                duration=139,
                genre="Comedy",
                rating="R",
                description="A middle-aged Chinese immigrant is swept up into an insane adventure in which she alone can save existence.",
                release_date=datetime(2022, 3, 25)
            ),
        ]

        for movie in movies:
            db.add(movie)
        db.commit()
        print(f"✅ Seeded {len(movies)} movies")

        # Seed cinemas
        print("🏢 Seeding cinemas...")
        cinemas = [
            Cinema(number=1, type="standard", total_seats=120, location="Ground Floor - East Wing", features=["Digital Sound", "Stadium Seating"]),
            Cinema(number=2, type="standard", total_seats=150, location="Ground Floor - West Wing", features=["Digital Sound", "Stadium Seating"]),
            Cinema(number=3, type="premium", total_seats=100, location="Second Floor - North", features=["Dolby Atmos", "Leather Recliners", "Cup Holders"]),
            Cinema(number=4, type="standard", total_seats=180, location="Ground Floor - Center", features=["Digital Sound", "Stadium Seating"]),
            Cinema(number=5, type="premium", total_seats=90, location="Second Floor - South", features=["Dolby Atmos", "Luxury Seating", "Extra Legroom"]),
            Cinema(number=6, type="imax", total_seats=300, location="Third Floor - IMAX Theater", features=["IMAX Screen", "IMAX Sound System", "Reserved Seating"]),
            Cinema(number=7, type="standard", total_seats=140, location="Ground Floor - South Wing", features=["Digital Sound", "Stadium Seating"]),
            Cinema(number=8, type="vip", total_seats=50, location="Fourth Floor - VIP Lounge", features=["Reclining Seats", "Table Service", "Premium Bar", "Gourmet Menu"]),
            Cinema(number=9, type="standard", total_seats=160, location="Second Floor - East", features=["Digital Sound", "Stadium Seating"]),
            Cinema(number=10, type="premium", total_seats=110, location="Second Floor - West", features=["Dolby Digital", "Luxury Seating", "Wide Screens"]),
            Cinema(number=11, type="standard", total_seats=200, location="Ground Floor - Main Hall", features=["Digital Sound", "Stadium Seating", "Large Screen"]),
            Cinema(number=12, type="standard", total_seats=130, location="Second Floor - Center", features=["Digital Sound", "Stadium Seating"]),
            Cinema(number=13, type="premium", total_seats=80, location="Third Floor - Premium Suite", features=["THX Certified", "Heated Seats", "Premium Sound"]),
            Cinema(number=14, type="standard", total_seats=170, location="Ground Floor - North Wing", features=["Digital Sound", "Stadium Seating"]),
            Cinema(number=15, type="imax", total_seats=280, location="Third Floor - IMAX Dome", features=["IMAX Dome", "Immersive Sound", "Reserved Seating"]),
            Cinema(number=16, type="standard", total_seats=145, location="Second Floor - Corner", features=["Digital Sound", "Stadium Seating"]),
            Cinema(number=17, type="vip", total_seats=60, location="Fourth Floor - Executive", features=["Massage Chairs", "Personal Service", "Premium Concessions"]),
            Cinema(number=18, type="premium", total_seats=95, location="Third Floor - East", features=["Dolby Vision", "Reclining Seats", "Enhanced Sound"]),
            Cinema(number=19, type="standard", total_seats=155, location="Ground Floor - Corner", features=["Digital Sound", "Stadium Seating"]),
            Cinema(number=20, type="premium", total_seats=105, location="Third Floor - West", features=["4DX Technology", "Motion Seats", "Environmental Effects"]),
        ]

        for cinema in cinemas:
            db.add(cinema)
        db.commit()
        print(f"✅ Seeded {len(cinemas)} cinemas")

        print("🎉 Database seeding completed successfully!")
        print("📊 Summary:")
        print(f"   - Cinema Types: {len(cinema_types)}")
        print(f"   - Movies: {len(movies)}")
        print(f"   - Cinemas: {len(cinemas)}")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()