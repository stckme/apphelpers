=======
History
=======

0.94.0 (2024-03-06)
-------------------
* Added support for Piccolo ORM

0.93.1 (2023-01-20)
-------------------
* Fixed get_by_secondary_key of CachedModel

0.93.0 (2023-01-19)
-------------------
* Added secondary_key support for CachedModel

0.92.3 (2023-01-15)
-------------------
* Added @response_model for FastAPI endpoints

0.92.2 (2023-12-26)
-------------------
* Fixed operation_id generation

0.92.1 (2023-12-24)
-------------------
* Fixed _get_matched_keys access for ReadOnlyCachedModel

0.92.0 (2023-12-23)
-------------------
* site_ctx implementation for FastAPI
* user_agent directive for FastAPI & Hug
* ignore_site_ctx implementation for FastAPI & Hug
* count_matched_keys implementation for ReadOnlyCachedModel

0.91.0 (2023-12-22)
-------------------
* Breaking: moved apphelpers.sessions.whoami to apphelpers.rest.{hug/fastapi}.whoami
* New convenient decorators in apphelpers.rest.endpoint
* any_group_required and all_groups_required implementation for FastAPI
* Improved errors
* Other improvements and fixes
* Moved CI from travis to github actions

0.90.0 (2023-10-16)
-------------------
* Support for FastAPI framework.

0.34.2 (2023-09-04)
-------------------
* Email INTERNAL_EMAIL_DOMAINS will also restrict bcc email recipients.
* Fixed typo

0.34.0 (2023-09-01)
-------------------

* settings.INTERNAL_EMAIL_DOMAINS must me defined for email sending safety in
  non-prod env.
  e.g. INTERNAL_EMAIL_DOMAINS = ['example.com', 'example.org']
  allows sending emails to only address ending with example.com or example.org

0.33.5 (2023-08-08)
-------------------
* Reusable utility `format_msg` added in email module to format email message

0.33.4 (2023-08-08)
-------------------
* Support for optionally addding headers added to email message

0.33.3 (2023-08-04)
-------------------
* For site-bound sessions, restrict access if site_id is missing

0.33.2 (2023-07-20)
-------------------
* session destroy fix for site-bound sessions

0.33.1 (2023-07-20)
-------------------
* site_id check fix for site-bound sessions

0.33.0 (2023-05-23)
-------------------
* Support for new directives: user_groups, user_site_groups, user_site_ctx
* Ambiguously named groups_required decorator is now replaced with any_group_required
* New decorator: all_groups_required

0.32.1 (2023-04-18)
-------------------
* Support for resyncing & destroying context bound session

0.32.0 (2023-04-11)
-------------------
* Support for context bound sessions

0.31.2 (2022-12-15)
-------------------
* Implement ReadWriteCachedModel.decrement()

0.31.1 (2022-09-20)
-------------------
* Extend sesion timeout fix for lookup key
* Implement sessions.sid2uid()

0.31.0 (2022-08-08)
-------------------
* Rename Config directive MD_* to SMTP_*

0.21.1 (2022-06-09)
-------------------
* Fix for SMTP+SSL connection

0.21.0 (2022-05-18)
-------------------
* applogger: general purpose application logging

0.20.0 (2022-04-29)
-------------------
* Support for custom authorizaion

0.19.1 (2021-10-07)
-------------------

* Report function args in honeybadger context

0.9.2 (2019-05-20)
------------------

* New options `groups_forbidden` and `groups_required` to secure API access

0.1.0 (2019-03-24)
------------------

* First release on PyPI.
