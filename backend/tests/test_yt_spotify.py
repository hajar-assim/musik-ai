import pytest
from backend.yt_spotify import clean_youtube_title, parse_artist_and_track


class TestCleanYoutubeTitle:
    """Tests for clean_youtube_title function"""

    def test_removes_official_video(self):
        assert clean_youtube_title("Song Name [Official Video]") == "Song Name"
        assert clean_youtube_title("Song Name (Official Video)") == "Song Name"

    def test_removes_official_audio(self):
        assert clean_youtube_title("Song Name [Official Audio]") == "Song Name"
        assert clean_youtube_title("Song Name (Official Audio)") == "Song Name"

    def test_removes_lyrics(self):
        assert clean_youtube_title("Song Name [Lyrics]") == "Song Name"
        assert clean_youtube_title("Song Name (Lyric)") == "Song Name"

    def test_removes_quality_indicators(self):
        assert clean_youtube_title("Song Name [HD]") == "Song Name"
        assert clean_youtube_title("Song Name (HQ)") == "Song Name"
        assert clean_youtube_title("Song Name [4K]") == "Song Name"

    def test_removes_multiple_indicators(self):
        assert (
            clean_youtube_title("Song Name [Official Video] [HD]")
            == "Song Name"
        )
        assert (
            clean_youtube_title("Song Name (Official Music Video) (Lyrics)")
            == "Song Name"
        )

    def test_case_insensitive(self):
        assert clean_youtube_title("Song Name [official video]") == "Song Name"
        assert clean_youtube_title("Song Name [OFFICIAL VIDEO]") == "Song Name"

    def test_handles_extra_whitespace(self):
        assert clean_youtube_title("Song  Name   [Official Video]") == "Song Name"

    def test_empty_string(self):
        assert clean_youtube_title("") == ""

    def test_no_changes_needed(self):
        assert clean_youtube_title("Regular Song Title") == "Regular Song Title"


class TestParseArtistAndTrack:
    """Tests for parse_artist_and_track function"""

    def test_dash_separator(self):
        artist, track = parse_artist_and_track("Artist Name - Track Name")
        assert artist == "Artist Name"
        assert track == "Track Name"

    def test_em_dash_separator(self):
        artist, track = parse_artist_and_track("Artist Name  Track Name")
        assert artist == "Artist Name"
        assert track == "Track Name"

    def test_by_separator(self):
        artist, track = parse_artist_and_track("Track Name by Artist Name")
        assert artist == "Artist Name"
        assert track == "Track Name"

    def test_colon_separator(self):
        artist, track = parse_artist_and_track("Artist Name: Track Name")
        assert artist == "Artist Name"
        assert track == "Track Name"

    def test_with_official_video_tag(self):
        artist, track = parse_artist_and_track(
            "Artist Name - Track Name [Official Video]"
        )
        assert artist == "Artist Name"
        assert track == "Track Name"

    def test_complex_title(self):
        artist, track = parse_artist_and_track(
            "The Beatles - Hey Jude [Official Music Video] [HD]"
        )
        assert artist == "The Beatles"
        assert track == "Hey Jude"

    def test_no_pattern_match(self):
        artist, track = parse_artist_and_track("Random Video Title")
        assert artist is None
        assert track == "Random Video Title"

    def test_empty_string(self):
        artist, track = parse_artist_and_track("")
        assert artist is None
        assert track == ""

    def test_too_short_artist_or_track(self):
        # Single character artist/track should not be parsed
        artist, track = parse_artist_and_track("A - Track Name")
        assert artist == "A"
        assert track == "Track Name"

    def test_whitespace_handling(self):
        artist, track = parse_artist_and_track("  Artist Name  -  Track Name  ")
        assert artist == "Artist Name"
        assert track == "Track Name"
