
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** qumail-backend
- **Date:** 2025-10-18
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001
- **Test Name:** health check endpoint returns complete service status
- **Test Code:** [TC001_health_check_endpoint_returns_complete_service_status.py](./TC001_health_check_endpoint_returns_complete_service_status.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/e2265849-69ec-48c4-aafc-dd2b45da2ed7/ae8cc7ca-e89b-4077-bca8-8ffb2c9966ac
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002
- **Test Name:** root endpoint provides api information and features
- **Test Code:** [TC002_root_endpoint_provides_api_information_and_features.py](./TC002_root_endpoint_provides_api_information_and_features.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/e2265849-69ec-48c4-aafc-dd2b45da2ed7/257da181-171f-40c3-9f5a-5b9b6a148e50
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003
- **Test Name:** get emails endpoint returns emails from specified folder
- **Test Code:** [TC003_get_emails_endpoint_returns_emails_from_specified_folder.py](./TC003_get_emails_endpoint_returns_emails_from_specified_folder.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 65, in <module>
  File "<string>", line 19, in test_get_emails_from_specified_folder
AssertionError: Expected status code 200, got 401

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/e2265849-69ec-48c4-aafc-dd2b45da2ed7/802c7340-da1c-4a95-8755-f1f8f5a6f724
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004
- **Test Name:** send encrypted email with valid security level
- **Test Code:** [TC004_send_encrypted_email_with_valid_security_level.py](./TC004_send_encrypted_email_with_valid_security_level.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 66, in <module>
  File "<string>", line 34, in test_send_encrypted_email_with_valid_security_level
AssertionError: Expected status code 200, got 401

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/e2265849-69ec-48c4-aafc-dd2b45da2ed7/e4dd8597-aff2-4034-b4ab-8ecf4884f36d
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005
- **Test Name:** encryption status endpoint returns real time quantum key metrics
- **Test Code:** [TC005_encryption_status_endpoint_returns_real_time_quantum_key_metrics.py](./TC005_encryption_status_endpoint_returns_real_time_quantum_key_metrics.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/e2265849-69ec-48c4-aafc-dd2b45da2ed7/6839e387-d15c-42a9-9db4-f0f7e079ed52
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006
- **Test Name:** generate quantum keys endpoint creates keys on both kmes
- **Test Code:** [TC006_generate_quantum_keys_endpoint_creates_keys_on_both_kmes.py](./TC006_generate_quantum_keys_endpoint_creates_keys_on_both_kmes.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/e2265849-69ec-48c4-aafc-dd2b45da2ed7/c89dd97c-c3ba-46f1-8df4-8f0c008b2495
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007
- **Test Name:** quantum status dashboard redirects to static html page
- **Test Code:** [TC007_quantum_status_dashboard_redirects_to_static_html_page.py](./TC007_quantum_status_dashboard_redirects_to_static_html_page.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 28, in <module>
  File "<string>", line 14, in test_tc007_quantum_status_dashboard_redirect
AssertionError: Expected status code 307 for redirect but got 200

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/e2265849-69ec-48c4-aafc-dd2b45da2ed7/5575091a-7061-40f9-b5ac-2bc13a314518
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **57.14** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---