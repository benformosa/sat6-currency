
* [ ] Allow importing script as function
** [ ] Rename to replace hyphen with underscore
** [x] Move commandline arguments to if __name__ == "__main__":
** [x] Return structured data from *_currency functions
*** [x] Print structured data using a formatter in __main__
** [ ] Write a TEST!!!

* [ ] Write a patchsummary.py which imports sat6-currency
** Summarise which systems are patched
** Print a report for each system with columns:
*** system_id
*** org_name
*** name
*** patched/not patched (based on score)
*** needs rebooting (based on traces)
*** compliant (if score and traces both 0)
*** lifecycle_environment
*** os_release
*** subscription_status
*** comment

* [ ] Add option to list traces. use /api/hosts/{}/traces {"total":x,...}

* [ ] Tests using unittest

* [ ] simple_currency
** [ ] after for host in hosts, invert the if statement and continue if the expression is false. that way, will be able to dedent the content of the for block after that
** [ ] tidy up line continuations using parentheses in value assignment
* [x] split score calculations into function
* [ ] change sys.exit to exception
