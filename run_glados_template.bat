@ECHO off
TITLE GLADOS

REM set "automation_fails_only=-a" %= Comment line out to turn off automation fails only =%
set "browser=-b chrome" %= Default browser to use when one cannot be determined from test run configuration =%
REM set "test_category_filters=-c user_scenarios -c seo -c light_regression -c tracking_code_metrics -c single_code_source -c smoke_test -c no_label -c compatibility -c design_ui -c data_content -c logic -c functional -c security -c performance"
REM set "no_test_category_filters=-n smoke_test"
set "developer_mode=-d" %= Comment line out to turn off developer mode =%
set "environment=-e stg1"
set "test_status_filters=-f passed -f blocked -f failed -f retest -f not_applicable -f untested"
set "pool_size=-p 4"    %= Recommended is 4 =%
set "remote_url=-r http://qaaew707-vm.carsdirect.win:4444/wd/hub"    %= Comment this line out to run locally =%
set "test_run_ids=-t 78871"    %= Give numbers separated by spaces =%
set "search_path=-s .\.." %= Give file path to location for Glados to search for suites =%
REM set "variables=-v dummy_var:value -v dummy_var2:value2" %= Comment line out if no custom variables =%
@ECHO on

py -3 .\resources\glados.py^
 %automation_fails_only%^
 %browser%^
 %test_category_filters%^
 %no_test_category_filters%^
 %developer_mode%^
 %environment%^
 %test_status_filters%^
 %pool_size%^
 %remote_url%^
 %test_run_ids%^
 %search_path%^
 %variables%
pause
EXIT


