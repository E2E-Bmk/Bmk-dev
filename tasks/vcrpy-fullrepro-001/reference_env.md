# vcrpy Reference Environment v1

The Stage 3 reference gate uses local `pytest-httpbin` HTTP/HTTPS fixtures.

Before running `score_pytest_original.py` for this task, set:

```powershell
$env:REQUESTS_CA_BUNDLE = "G:\research\01_agents\swe-e2e\envs\sqlite-utils-score\Lib\site-packages\pytest_httpbin\certs\client.pem"
$env:NO_PROXY = "*"
$env:no_proxy = "*"
Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:ALL_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue
Remove-Item Env:all_proxy -ErrorAction SilentlyContinue
```

Without the CA bundle, parameterized HTTPS cases from `httpbin_both` fail in
the reference implementation. Without proxy clearing, local `httpbin.org`
DNS override tests can be routed through an external proxy and fail with
transport errors unrelated to VCR.py behavior.
