1. Find the latest releast tag `v**` and use it as the base tag
2. Generate release note under /releases folder in markdown format
3. Ask to confirm the release note, once confirmed, run /precommit command to validate everything working
4. Git commit the release note if the only change is the relese note md file
5. Create a new release version following the sementic version convention and git push the release
