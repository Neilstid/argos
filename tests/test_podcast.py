from unittest.mock import MagicMock, patch
import numpy as np
import os
from app.utils.podcast import synth_podcast_kokoro

def test_synth_podcast_kokoro_sample_rate(tmp_path):
    audio_file = os.path.join(tmp_path, "test.mp3")
    
    mock_pipeline = MagicMock()
    # Generator returns (gs, ps, audio)
    mock_pipeline.return_value = [("gs", "ps", np.zeros(24000, dtype=np.float32))]
    
    with patch("app.utils.podcast.KPipeline", return_value=mock_pipeline), \
         patch("app.utils.podcast.sf.write") as mock_sf_write:
        
        podcast = {
            "turns": [
                {"speaker": "Anna", "text": "Hello world"}
            ]
        }
        
        synth_podcast_kokoro(podcast, audio_file)
        
        mock_sf_write.assert_called_once()
        args, kwargs = mock_sf_write.call_args
        written_path, merged_audio, sample_rate = args
        
        assert written_path == audio_file
        assert sample_rate == 24000, f"Expected sample rate 24000, got {sample_rate}"
