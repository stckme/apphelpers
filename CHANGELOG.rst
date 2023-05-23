=======
History
=======

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
