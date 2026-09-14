from unittest.mock import MagicMock, patch

from app.run_local import main


@patch("app.run_local.time.sleep", side_effect=KeyboardInterrupt)
@patch("app.run_local.subprocess.Popen")
def test_launcher_starts_and_stops_api_and_worker(mock_popen, _):
    api, worker = MagicMock(), MagicMock()
    api.poll.return_value = None
    worker.poll.return_value = None
    mock_popen.side_effect = [api, worker]

    assert main() == 0
    assert mock_popen.call_count == 2
    api.terminate.assert_called_once()
    worker.terminate.assert_called_once()
