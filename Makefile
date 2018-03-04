
default:	test2_diff

help:	## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

TEST1 = ./an-import-people.py -v -d tests/an-import-test1.csv

# Use log
TEST2_TMP = tests/an-import-test2.tmp
TEST2 = head -n 10 tests/an-import-test2.out > $(TEST2_TMP); ./an-import-people.py -v --skip --dryrun --logfile $(TEST2_TMP) tests/an-import-test1.csv; cat $(TEST2_TMP)

test: test1_diff test2_diff ## Run all tests

test1:	## Dry run test1
	$(TEST1)

test1_diff:	## Dry run test1 (diff against baseline test)
	$(TEST1) | diff tests/an-import-test1.out -

test1_rebase:	## Create new output baseline for test1
	$(TEST1) > tests/an-import-test1.out

test2:	## Dry run test2
	$(TEST2)

test2_diff:	## Dry run test2 (diff against baseline test)
	$(TEST2) | diff tests/an-import-test2.out -

test2_rebase:	## Create new output baseline for test2
	$(TEST2) > tests/an-import-test2.out
