import subprocess
import time
import xml.etree.ElementTree as etree

import ejudge_util


def grader(response, grader_payload):
    contest_id = ejudge_util.get_contest_id(grader_payload['contest_name'])
    problem_exist = ejudge_util.problem_exist(contest_id,
                                              grader_payload['problem_name'])
    if not contest_id or not problem_exist:
        ejudge_util.create_task(grader_payload)
    check_payload = ejudge_util.check_grader_payload(grader_payload,
                                                     ejudge_util.get_contest_path(
                                                         contest_id),
                                                     grader_payload[
                                                         'problem_name'])
    if check_payload != 0:
        ejudge_util.update_payload(check_payload, grader_payload)
        print 'Test and answer data update'
    result = run_grade_in_ejudge(response, grader_payload)
    return result


def run_grade_in_ejudge(response, grader_payload):
    response_file = open('response.txt', 'w')
    response_file.write(response)
    response_file.close()
    contest_id = ejudge_util.get_contest_id(grader_payload['contest_name'])
    problem_name = grader_payload['problem_name']
    lang = grader_payload['lang_short_name']
    run_id, err = subprocess.Popen(["/opt/ejudge/bin/ejudge-contests-cmd",
                                    str(contest_id),
                                    "submit-run",
                                    "/home/ejudge/session.pwd",
                                    problem_name,
                                    lang,
                                    'response.txt'],
                                   stdout=subprocess.PIPE).communicate()

    run_id = run_id.replace('/n', ' ').strip()
    name_report_file = 'report_' + run_id + '.xml'
    contest_path = ejudge_util.get_contest_path(contest_id)
    command_dump_report = '/opt/ejudge/bin/ejudge-contests-cmd ' + str(
        contest_id) + ' dump-report' + ' /home/ejudge/session.pwd ' + run_id + ' >' + contest_path + 'report/' + name_report_file
    # КОСТЫЛЬ.это время, за которое еджадж должен проверить работу. сделать проверку в цикле
    time.sleep(2)
    subprocess.call(command_dump_report, shell=True)
    result = pars_report(name_report_file, contest_path)
    return result


def pars_report(name_report_file, contest_path):
    result = dict()
    del_str_in_report_xml(contest_path, name_report_file)
    result_xml = etree.parse(contest_path + 'report/' + name_report_file)
    test_tag = result_xml.getroot().find("tests").findall("test")
    checker_list = list()
    test_ok = 0
    for i in test_tag:
        checker_list.append(i.find("checker"))
    for checker in checker_list:
        if checker.text.strip().find('OK') != -1:
            test_ok += 1
    print test_ok, checker_list
    if test_ok != len(checker_list):
        result['success'] = False
        result['score'] = 0
    else:
        result['success'] = True
        result['score'] = 1
    compiler_out = result_xml.getroot().find("compiler_output").text
    if compiler_out:
        result['compiler_output'] = compiler_out
    print "Report pars.\nresult=", result
    return result


def del_str_in_report_xml(contest_path, name_report):
    report_full_name = contest_path + 'report/' + name_report
    file_r = open(report_full_name, 'r')
    f_line = list()
    for line in file_r:
        f_line.append(line)
    file_r.close()
    f = open(report_full_name, 'w')
    for line in f_line[2:]:
        f.write(line)
    f.close()
