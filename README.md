CTXCTL-CONTRIB
==============

This repository is a set of useful implementations that can be shared among ctxctl users.

I want to contribute!
=====================

If you have a code that can be useful to another ctxctl user, you should share it!

  - make sure your code is generic enough to be used by others.
  - make sure your code is not already in the repository.

If you don't have a code to share, but you are willing to work in something for the greater good, check the issues page to see what we need. :)

How to contribute?
==================

Here, Git!

There is one eternal branch: master.
Features are generally branched off from master and merged back into master when they are ready.
We use feature branches to developing new features. Everytime you want to add a code you should:
  - create an issue
  - create a branch to work on, you can branch `master` or another feature branch that was not merged into `master` yet
  - do your work on the branch
  - pull modifications from the `master` branch and resolve conflicts
  - create a merge request to `master`

About doing your work:
----------------------

Make atomic commits as you develop the feature. Try to keep the branch short-lived. Push often!
When developing the feature, make sure to follow the style guide and to add unit tests.
When done, ask for the merge request, wait the review, address the comments (if exist) and be happy.

commit:
-------
Good commit hygiene makes it easier to understand how the code changes over time and fix issues as they appear.
It also saves time during code review when the development of a feature and the decisions being made are documented in the commit messages instead of being hidden behind a wall of code.
A good, minimal commit has the following characteristics:
  - The commit message header succinctly describes the change introduced in the commit. 
  - It contains only logically related changes in the code. "add something here" and "fix something there" are not good commit messages.
  - Each commit must leave the code in a working state.

How to get started: 
---------
- Install [`CTXCTL Primer`](http://ai-ctx.gitlab.io/ctxctl/primer.html#).
- Clone `ctxctl_contrib` inside the parent folder of /cortexcontrol 
```
git clone https://code.ini.uzh.ch/ncs/libs/ctxctl_contrib.git
```
- Copy `run_rpyc.py` from ctxctl_contrib/ to cortexcontrol/


