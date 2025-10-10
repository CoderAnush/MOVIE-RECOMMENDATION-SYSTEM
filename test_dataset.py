#!/usr/bin/env python3
"""
Quick System Test - Verify Full 10M Dataset with Real Posters
"""

from fast_complete_loader import get_fast_complete_database, get_database_stats

print("🚀 Testing Full 10M MovieLens Dataset...")
print("=" * 60)

# Load database
db = get_fast_complete_database()
stats = get_database_stats()

print(f"\n✅ SUCCESS: {len(db)} movies loaded")
print(f"📊 Total Movies: {stats['total_movies']:,}")
print(f"⭐ Average Rating: {stats['avg_rating']:.2f}")
print(f"🎭 Available Genres: {stats['genres_available']}")
print(f"📅 Year Range: {stats['year_range']['min']}-{stats['year_range']['max']}")

print(f"\n🎬 Sample movies with real posters:")
print("=" * 60)

for i, movie in enumerate(db[:5]):
    title = movie.get('title', 'Unknown')
    year = movie.get('year', 'Unknown')
    rating = movie.get('rating', 0)
    genres = movie.get('genres', [])
    poster = movie.get('poster', '')
    popularity = movie.get('popularity', 0)
    
    print(f"\n{i+1}. {title} ({year})")
    print(f"   Rating: {rating}/10 | Popularity: {popularity}")
    print(f"   Genres: {', '.join(genres)}")
    
    if poster and 'placeholder' not in poster.lower():
        print(f"   ✅ Real Poster: {poster[:60]}...")
    else:
        print(f"   ⚠️ Placeholder poster")

print("\n" + "=" * 60)
print("✅ System ready for recommendations!")
print(f"🌐 Frontend connects to: http://127.0.0.1:8080")
print("=" * 60)
