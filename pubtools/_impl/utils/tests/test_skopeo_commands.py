try:
    import mock
except ImportError:
    from unittest import mock

import paramiko
import pytest

from pubtools._impl.utils.executor import skopeo


@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._add_file")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
@mock.patch("pubtools._impl.utils.executor.os.path.isdir")
@mock.patch("pubtools._impl.utils.executor.docker.tls.TLSConfig")
@mock.patch("pubtools._impl.utils.executor.APIClient")
def test_container_executor_skopeo_login(
    mock_api_client, mock_tls_config, mock_isdir, mock_run_cmd, mock_add_file
):
    mock_create_container = mock.MagicMock()
    mock_create_container.return_value = {"Id": "123"}
    mock_api_client.return_value.create_container = mock_create_container
    mock_start = mock.MagicMock()
    mock_api_client.return_value.start = mock_start
    mock_remove_container = mock.MagicMock()
    mock_api_client.return_value.remove_container = mock_remove_container
    mock_isdir.return_value = True

    mock_run_cmd.side_effect = [
        ("not logged in", "nothing"),
        ("Login Succeeded", "nothing"),
    ]

    with skopeo.SkopeoContainerExecutor(
        "quay.io/some/image:1",
        base_url="some-url.com",
        timeout=120,
        verify_tls=True,
        cert_path="/some/path",
    ) as executor:
        executor.commands.skopeo_login("some-name", "some-password")

    assert mock_run_cmd.call_count == 2
    assert mock_run_cmd.call_args_list[0] == mock.call(
        "skopeo login --get-login quay.io", tolerate_err=True
    )
    assert mock_run_cmd.call_args_list[1] == mock.call(
        " sh -c 'cat /tmp/skopeo_password.txt | skopeo login --authfile $HOME/.docker/config.json "
        "-u some-name --password-stdin quay.io'"
    )
    mock_add_file.assert_called_once_with("some-password", "skopeo_password.txt")


@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._add_file")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
@mock.patch("pubtools._impl.utils.executor.os.path.isdir")
@mock.patch("pubtools._impl.utils.executor.docker.tls.TLSConfig")
@mock.patch("pubtools._impl.utils.executor.APIClient")
def test_container_executor_skopeo_login_already_logged(
    mock_api_client, mock_tls_config, mock_isdir, mock_run_cmd, mock_add_file
):
    mock_create_container = mock.MagicMock()
    mock_create_container.return_value = {"Id": "123"}
    mock_api_client.return_value.create_container = mock_create_container
    mock_start = mock.MagicMock()
    mock_api_client.return_value.start = mock_start
    mock_remove_container = mock.MagicMock()
    mock_api_client.return_value.remove_container = mock_remove_container
    mock_isdir.return_value = True

    mock_run_cmd.return_value = ("some-name", "nothing")

    with skopeo.SkopeoContainerExecutor(
        "quay.io/some/image:1",
        base_url="some-url.com",
        timeout=120,
        verify_tls=True,
        cert_path="/some/path",
    ) as executor:
        executor.commands.skopeo_login("some-name", "some-password")

    mock_run_cmd.assert_called_once_with(
        "skopeo login --get-login quay.io", tolerate_err=True
    )
    mock_add_file.assert_not_called()


@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._add_file")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
@mock.patch("pubtools._impl.utils.executor.os.path.isdir")
@mock.patch("pubtools._impl.utils.executor.docker.tls.TLSConfig")
@mock.patch("pubtools._impl.utils.executor.APIClient")
def test_container_executor_skopeo_login_missing_credential(
    mock_api_client, mock_tls_config, mock_isdir, mock_run_cmd, mock_add_file
):
    mock_create_container = mock.MagicMock()
    mock_create_container.return_value = {"Id": "123"}
    mock_api_client.return_value.create_container = mock_create_container
    mock_start = mock.MagicMock()
    mock_api_client.return_value.start = mock_start
    mock_remove_container = mock.MagicMock()
    mock_api_client.return_value.remove_container = mock_remove_container
    mock_isdir.return_value = True

    mock_run_cmd.side_effect = [
        ("not logged in", "nothing"),
        ("Login Succeeded", "nothing"),
    ]

    with skopeo.SkopeoContainerExecutor(
        "quay.io/some/image:1",
        base_url="some-url.com",
        timeout=120,
        verify_tls=True,
        cert_path="/some/path",
    ) as executor:
        with pytest.raises(
            ValueError, match="Skopeo login credentials are not present.*"
        ):
            executor.commands.skopeo_login("some-name")

    mock_run_cmd.assert_called_once_with(
        "skopeo login --get-login quay.io", tolerate_err=True
    )
    mock_add_file.assert_not_called()


@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._add_file")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
@mock.patch("pubtools._impl.utils.executor.os.path.isdir")
@mock.patch("pubtools._impl.utils.executor.docker.tls.TLSConfig")
@mock.patch("pubtools._impl.utils.executor.APIClient")
def test_container_executor_skopeo_login_fail(
    mock_api_client, mock_tls_config, mock_isdir, mock_run_cmd, mock_add_file
):
    mock_create_container = mock.MagicMock()
    mock_create_container.return_value = {"Id": "123"}
    mock_api_client.return_value.create_container = mock_create_container
    mock_start = mock.MagicMock()
    mock_api_client.return_value.start = mock_start
    mock_remove_container = mock.MagicMock()
    mock_api_client.return_value.remove_container = mock_remove_container
    mock_isdir.return_value = True

    mock_run_cmd.side_effect = [
        ("not logged in", "nothing"),
        ("Login Failed", "nothing"),
    ]

    with skopeo.SkopeoContainerExecutor(
        "quay.io/some/image:1",
        base_url="some-url.com",
        timeout=120,
        verify_tls=True,
        cert_path="/some/path",
    ) as executor:
        with pytest.raises(
            RuntimeError, match="Login command didn't generate expected output.*"
        ):
            executor.commands.skopeo_login("some-name", "some-password")

    assert mock_run_cmd.call_count == 2
    assert mock_run_cmd.call_args_list[0] == mock.call(
        "skopeo login --get-login quay.io", tolerate_err=True
    )
    assert mock_run_cmd.call_args_list[1] == mock.call(
        " sh -c 'cat /tmp/skopeo_password.txt | skopeo login --authfile $HOME/.docker/config.json "
        "-u some-name --password-stdin quay.io'"
    )
    mock_add_file.assert_called_once_with("some-password", "skopeo_password.txt")


@mock.patch("pubtools._impl.utils.executor.APIClient")
@mock.patch("pubtools._impl.utils.executor.LocalExecutorImpl._run_cmd")
def test_container_executor_skopeo_login_already_logged(mock_run_cmd, mock_api_client):
    executor = skopeo.SkopeoContainerExecutor("run-image:latest")

    mock_run_cmd.return_value = ("quay_user", "")
    executor.commands.skopeo_login("quay_user", "quay_token")
    mock_run_cmd.assert_called_once_with(
        "skopeo login --get-login quay.io", tolerate_err=True
    )


@mock.patch("pubtools._impl.utils.executor.APIClient")
@mock.patch("pubtools._impl.utils.executor.LocalExecutorImpl._run_cmd")
def test_container_executor_skopeo_login_missing_credentials(
    mock_run_cmd, mock_api_client
):
    executor = skopeo.SkopeoContainerExecutor("run-image:latest")

    mock_run_cmd.return_value = ("not logged into quay", "")
    with pytest.raises(ValueError, match=".*login credentials are not present.*"):
        executor.commands.skopeo_login()


@mock.patch("pubtools._impl.utils.executor.APIClient")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
def test_container_executor_skopeo_login_success(mock_run_cmd, mock_api_client):
    executor = skopeo.SkopeoContainerExecutor("run-image:latest")
    mock_api_client.return_value.exec_inspect.return_value = {"ExitCode": 0}
    mock_run_cmd.side_effect = [("not logged into quay", ""), ("Login Succeeded", "")]
    executor.commands.skopeo_login("quay_user", "quay_token")
    assert mock_run_cmd.call_args_list == [
        mock.call("skopeo login --get-login quay.io", tolerate_err=True),
        mock.call(
            " sh -c 'cat /tmp/skopeo_password.txt | skopeo login --authfile $HOME/.docker/config.json -u quay_user "
            "--password-stdin quay.io'",
        ),
    ]


@mock.patch("pubtools._impl.utils.executor.APIClient")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
def test_container_executor_skopeo_tag_images(mock_run_cmd, mock_api_client):
    executor = skopeo.SkopeoContainerExecutor("run-image:latest")
    mock_api_client.return_value.exec_inspect.return_value = {"ExitCode": 0}
    executor.commands.tag_images(
        "quay.io/repo/image:1", ["quay.io/repo/dest:1", "quay.io/repo/dest:2"]
    )
    assert mock_run_cmd.call_args_list == [
        mock.call(
            "skopeo copy docker://quay.io/repo/image:1 docker://quay.io/repo/dest:1"
        ),
        mock.call(
            "skopeo copy docker://quay.io/repo/image:1 docker://quay.io/repo/dest:2"
        ),
    ]


@mock.patch("pubtools._impl.utils.executor.APIClient")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
def test_container_executor_skopeo_tag_images_all_arch(mock_run_cmd, mock_api_client):
    executor = skopeo.SkopeoContainerExecutor("run-image:latest")
    mock_api_client.return_value.exec_inspect.return_value = {"ExitCode": 0}
    executor.commands.tag_images(
        "quay.io/repo/image:1", ["quay.io/repo/dest:1", "quay.io/repo/dest:2"], True
    )
    assert mock_run_cmd.call_args_list == [
        mock.call(
            "skopeo copy --all docker://quay.io/repo/image:1 docker://quay.io/repo/dest:1"
        ),
        mock.call(
            "skopeo copy --all docker://quay.io/repo/image:1 docker://quay.io/repo/dest:2"
        ),
    ]


@mock.patch("pubtools._impl.utils.executor.APIClient")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
def test_container_executor_skopeo_inspect(mock_run_cmd, mock_api_client):
    mock_run_cmd.return_value = ('{"aaa":"bbb"}', "")
    executor = skopeo.SkopeoContainerExecutor("run-image:latest")

    ret = executor.commands.skopeo_inspect("quay.io/repo/image:1")
    mock_run_cmd.assert_called_once_with("skopeo inspect docker://quay.io/repo/image:1")
    assert ret == {"aaa": "bbb"}

    ret = executor.commands.skopeo_inspect("quay.io/repo/image:1", raw=True)
    assert ret == '{"aaa":"bbb"}'


@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._add_file")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
@mock.patch("pubtools._impl.utils.executor.os.path.isdir")
@mock.patch("pubtools._impl.utils.executor.docker.tls.TLSConfig")
@mock.patch("pubtools._impl.utils.executor.APIClient")
def test_container_executor_skopeo_login_already_logged(
    mock_api_client, mock_tls_config, mock_isdir, mock_run_cmd, mock_add_file
):
    mock_create_container = mock.MagicMock()
    mock_create_container.return_value = {"Id": "123"}
    mock_api_client.return_value.create_container = mock_create_container
    mock_start = mock.MagicMock()
    mock_api_client.return_value.start = mock_start
    mock_remove_container = mock.MagicMock()
    mock_api_client.return_value.remove_container = mock_remove_container
    mock_isdir.return_value = True

    mock_run_cmd.return_value = ("some-name", "nothing")

    with skopeo.SkopeoContainerExecutor(
        "quay.io/some/image:1",
        base_url="some-url.com",
        timeout=120,
        verify_tls=True,
        cert_path="/some/path",
    ) as executor:
        executor.commands.skopeo_login("some-name", "some-password")

    mock_run_cmd.assert_called_once_with(
        "skopeo login --get-login quay.io", tolerate_err=True
    )
    mock_add_file.assert_not_called()


@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._add_file")
@mock.patch("pubtools._impl.utils.executor.ContainerExecutorImpl._run_cmd")
@mock.patch("pubtools._impl.utils.executor.os.path.isdir")
@mock.patch("pubtools._impl.utils.executor.docker.tls.TLSConfig")
@mock.patch("pubtools._impl.utils.executor.APIClient")
def test_container_executor_skopeo_login_missing_credential(
    mock_api_client, mock_tls_config, mock_isdir, mock_run_cmd, mock_add_file
):
    mock_create_container = mock.MagicMock()
    mock_create_container.return_value = {"Id": "123"}
    mock_api_client.return_value.create_container = mock_create_container
    mock_start = mock.MagicMock()
    mock_api_client.return_value.start = mock_start
    mock_remove_container = mock.MagicMock()
    mock_api_client.return_value.remove_container = mock_remove_container
    mock_isdir.return_value = True

    mock_run_cmd.side_effect = [
        ("not logged in", "nothing"),
        ("Login Succeeded", "nothing"),
    ]

    with skopeo.SkopeoContainerExecutor(
        "quay.io/some/image:1",
        base_url="some-url.com",
        timeout=120,
        verify_tls=True,
        cert_path="/some/path",
    ) as executor:
        with pytest.raises(
            ValueError, match="Skopeo login credentials are not present.*"
        ):
            executor.commands.skopeo_login("some-name")

    mock_run_cmd.assert_called_once_with(
        "skopeo login --get-login quay.io", tolerate_err=True
    )
    mock_add_file.assert_not_called()
