
default:	test1_diff

help:	## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

TEST1 = ./an-import-people.py -v -d tests/an-import-test1.csv

test1:	## Dry run test1 (diff against baseline test)
	$(TEST1)

test1_diff:	## Dry run test1 (diff against baseline test)
	$(TEST1) | diff tests/an-import-test1.out -

rebase:	## Create new output baseline for test1
	$(TEST1) > tests/an-import-test1.out
