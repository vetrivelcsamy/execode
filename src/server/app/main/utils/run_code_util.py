from __future__ import print_function
import os
import subprocess
import fileinput
import execjs
import multiprocessing

import sys
import threading
from time import sleep
try:
    import thread
except ImportError:
    import _thread as thread


def quit_function(fn_name):
    # print to stderr, unbuffered in Python 2.
    print('{0} took too long'.format(fn_name), file=sys.stderr)
    sys.stderr.flush() # Python 3 stderr is likely buffered.
    thread.interrupt_main() # raises KeyboardInterrupt

def exit_after(s):
    '''
    use as decorator to exit process if
    function takes longer than s seconds
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer


def makeRunCodeFolder(user_id):
    """
        Check if user run code folder exists: Creates if it doesnot
    """
    cwd = os.getcwd()
    path = cwd+"/static/run_code/user"+str(user_id)
    if os.path.exists(path):
        return path
    else:
        try:
            os.makedirs(path)
        except:
            return False
    return path


def make_python_codefile(code, path):
    wf = open(path+"/code.py", "w")
    wf.write(code)
    wf.close()
    return path+"/code.py"


def make_input_file(sample_input, path):
    wg = open(path+"/in.txt", "w")
    wg.write(sample_input)
    wg.close()
    return path+"/in.txt"


def make_sample_output(sample_output, path):
    wg = open(path+"/expected.txt", "w")
    wg.write(sample_output)
    wg.write("\n")
    wg.close()
    return path+"/expected.txt"


def make_js_file(code, path):
    wf = open(path+"/code.js", "w")
    wf.write(code)
    wf.close()
    return path+"/code.js"

def make_cpp_file(code, path):
    wf = open(path+"/code.cpp", "w")
    wf.write(code)
    wf.close()
    return path+"/code.cpp"

@exit_after(1)
def run_python_code(code_path, input_path, output_path, error_path):
    print("started run code")
    os.system("python3 %s 0<%s 1>%s 2>%s"%(
            code_path, input_path, output_path, error_path))

@exit_after(1)
def run_python2_code(code_path, input_path, output_path, error_path):
    print("started run code")
    os.system("python3 %s 0<%s 1>%s 2>%s"%(
            code_path, input_path, output_path, error_path))

@exit_after(1)
def run_cpp_code(code_path, input_path, output_path, error_path):
    print("started cpp run code")

    os.system('g++ %s -o %s 2>%s'%(code_path, code_path.strip('.cpp'), error_path))
    os.system("./%s <%s >%s "%(
            code_path.strip('.cpp'), input_path, output_path))

@exit_after(1)
def run_js_code(code, input_test):
    ctx = execjs.compile(code)
    temp_output = ctx.call('process', input_test)
    return temp_output

def generate_output_error(input_path, code_path, path, my_lang, output_file_name="out.txt", error_file_name="err.txt"):
    """
        Generate output and error
    """
    output_path = path+"/"+output_file_name+".txt"
    error_path = path+"/"+error_file_name+".txt"
    if my_lang == "javascript":
        f_code = open(code_path)
        f_input_test = open(input_path)
        code = f_code.read()
        input_test = f_input_test.read()
        try:
            temp_output = run_js_code(code, input_test)
        except Exception:
            return False, "Infinite Loop"
        f_output = open(output_path, "w")
        f_output.write(temp_output)
        f_output.close()
        f_error = open(error_path ,'w')
        f_error.close()

    elif my_lang == "python":
        try:
            run_python_code(
            code_path, input_path, output_path, error_path)
        except Exception as e:
            return False, "Infinite Loop"

    elif my_lang == "python2":
        try:
            run_python2_code(
            code_path, input_path, output_path, error_path)
        except Exception as e:
            return False, "Infinite Loop"
    
    elif my_lang == "cpp":
        try:
            run_cpp_code(
            code_path, input_path, output_path, error_path)
        except Exception as e:
            return False, "Infinite Loop"

    return output_path, error_path


def is_error(error_path):
    wf = open(error_path)
    lines = wf.readlines()
    if len(lines) == 0:
        wf.close()
        return False
    else:
        wf.close()
        return True


def read_error(error_path):
    wf = open(error_path)
    lines = wf.readlines()
    wf.close()
    return lines


def compare_output(output_path, expected_path):
    user_output = open(output_path)
    expected_output = open(expected_path)
    output_lines = user_output.readlines()
    expected_lines = expected_output.readlines()
    user_output.close()
    expected_output.close()
    # print(expected_lines)
    if len(output_lines) == len(expected_lines):
        for i in range(len(output_lines)):
            if output_lines[i] != expected_lines[i]:
                return False, output_lines
        return True, output_lines
    else:
        return False, output_lines


def getResults(sample_input, sample_output, language, user_id, code):
    #if language == 'javascript':
    #    output_boolean = False
    #    error = ''
    #    ctx = execjs.compile(code)
    #    temp_output = ctx.call('process', sample_input)
    #    if temp_output == sample_output:
    #        output_boolean = True
    #    return temp_output, error, output_boolean

    path = makeRunCodeFolder(user_id)
    my_lang = language.lower()
    if path:
        input_path = make_input_file(sample_input, path)
        expected_path = make_sample_output(sample_output, path)

        if my_lang == "javascript":
            code_file_path = make_js_file(code, path)
        elif my_lang == "python":
            code_file_path = make_python_codefile(code, path)
        elif my_lang == 'cpp':
            code_file_path = make_cpp_file(code, path)

        output_path, error_path = generate_output_error(
            input_path, code_file_path, path, my_lang)

        if output_path == False:
            return False, "Infinite Loop", False

        is_correct, output = compare_output(output_path, expected_path)
        return (''.join(output), read_error(error_path), is_correct and (not is_error(error_path)))

    return None, None, False
