# 83-01 Summary

- Added a frontend harvest bridge that writes draft dataset packs through the active artifact root
  instead of relying on direct browser filesystem access.
- `/analysis` can now export the current filtered case or delta selection as a draft dataset pack
  with deterministic output stems and route-local success/error messaging.
