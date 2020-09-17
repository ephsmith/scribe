from flask import Flask
from flask import request
from flask import render_template
import logging

logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)


f1819 = """ACCT 1010 Principles of Accounting I
FSED 1010 History and Sociology of Funeral Service
FSED 1020 Dynamics of Grief Management
FSED 1030 Funeral Directing
FSED 1040 Funeral Directing Practicum I
FSED 1050 Funeral Directing Practicum II
FSED 1060 Mortuary Law and Ethics
FSED 1070 Funeral Service Merchandising
FSED 1080 Chemistry of Funeral Service
FSED 2010 Funeral Home Management
FSED 2020 Embalming I
FSED 2030 Embalming Practicum I
FSED 2040 Embalming II
FSED 2050 Embalming Practicum II
FSED 2060 Restorative Art
FSED 2070 Microbiology and Pathology for Funeral Service
FSED 2080 Funeral Service Seminar"""

f1920 = """ACCT 1010 Principles of Accounting I
FSED 1010 History and Sociology of Funeral Service
FSED 1020 Dynamics of Grief Management
FSED 1030 Funeral Directing
FSED 1040 Funeral Directing Practicum
FSED 1060 Mortuary Law and Ethics
FSED 1070 Funeral Service Merchandising
FSED 1080 Chemistry of Funeral Service
FSED 2010 Funeral Home Management
FSED 2020 Embalming I
FSED 2030 Embalming Practicum I
FSED 2040 Embalming II
FSED 2050 Embalming Practicum II
FSED 2060 Restorative Art
FSED 2070 Microbiology and Pathology for Funeral Service
FSED 2080 Funeral Service Seminar
FSED 2100 Anatomy for Funeral Service"""


def catparse(text):
    """
    parses a plain text list of courses (as copied from
    catalog.southwest and returns a list of course dicts in scribe format.
    """
    lst_out = []
    in_or = False
    crs_last = True
    stack = []
    for line in text.splitlines():
        if not line.strip():            # ignore blank lines
            continue
        if "or" == line.strip().lower():
            logging.debug('OR FOUND')
            in_or = True
            crs_last = False
            continue

        elif crs_last:
            if stack and in_or:
                # reached the end of an OR. push stack
                logging.debug('END OF OR')
                if len(stack) > 1:
                    lst_out.append(stack)
                else:
                    lst_out += stack
                    in_or = False
            else:
                lst_out += stack
            stack = []
        lst = line.strip().split()
        logging.debug(f'lst -> {lst}')
        course = {'subject': lst[0],
                  'number': lst[1],
                  'title': ' '.join(lst[2:])}
        stack += [course]
        crs_last = True

    if len(stack) > 1:
        lst_out.append(stack)
    else:
        lst_out += stack
    logging.debug(lst_out.__repr__())
    return lst_out


def catstring(lst):
    """
    converts a list (as produced by catparse) to a scribe string
    """
    fmt = '1 class in {subject} {number}\n' \
          '  label {n} "{title}"\n'
    n = 0
    out = ''
    lst = sorted(lst, key=lambda x: ''.join([x['subject'], x['number']]))
    for course in lst:
        logging.debug(f'catstring: n={n},\n\tcourse={course}')
        if isinstance(course, dict):
            out += fmt.format(**course, n=n)
            n += 1
        elif isinstance(course, list):
            crsub = ', '.join([' '.join([c['subject'], c['number']])
                               for c in course])
            titles = ' or '.join([c['title'] for c in course])
            out += f'1 class in {crsub}\n'
            out += f'  label {n} "{titles}"\n'
            n += 1
    return out


def transcode(text):
    """
    calls catparse and catstring to converts catalog formatted
    text to scribe formatted rules
    """
    lst = catparse(text)
    return catstring(lst)


def all_courses(lst, out=None):
    """
    returns a set of all courses from a list as returned by catparse.

    NOTE: This does not rely on course titles due to potential data
    inconsistency.
    """
    if out is None:
        out = set()
    for c in lst:
        if isinstance(c, dict):
            out.add(' '.join([c['subject'], c['number']]))
        else:
            all_courses(c, out)
    return out


def get_courses(text):
    """
    calls catparse and all_courses to return a set of courses
    from text
    """
    return all_courses(catparse(text))


def set_lst(cset, clst):
    """
    returns a list of elements from clst that have matching course
    subject,number pairs in cset
    """

    return list(filter(lambda x: ' '.join([x['subject'], x['number']])
                       in cset, clst))


def diff_course_lists(txt_a, txt_b):
    """
    returns course lists:

    a, b, a intersect b, a-b, b-a
    """
    lst_a, lst_b = catparse(txt_a), catparse(txt_b)
    set_a, set_b = all_courses(lst_a), all_courses(lst_b)

    a_int_b = (set_a & set_b)
    a_b = set_a - set_b
    b_a = set_b - set_a

    return lst_a, lst_b, set_lst(a_int_b, lst_a),\
        set_lst(a_b, lst_a), set_lst(b_a, lst_b)


@app.route('/concdiff', methods=['POST', 'GET'])
def conc_diff_app():
    if request.method == 'POST':
        txt_a = request.form['pasted_A']
        txt_b = request.form['pasted_B']
        label_a = request.form['label_a'] or 'Group A'
        label_b = request.form['label_b'] or 'Group B'
        lst_a, lst_b, a_int_b, a_b, b_a = diff_course_lists(txt_a, txt_b)
        str_ab, str_ba = catstring(a_b), catstring(b_a)
        str_a_int_b = catstring(a_int_b)
        return render_template('concdiff.html',
                               a_b=str_ab,
                               b_a=str_ba,
                               label_a=label_a,
                               label_b=label_b,
                               a_int_b=str_a_int_b,
                               pasted_A=request.form['pasted_A'],
                               pasted_B=request.form['pasted_B'])

    else:
        return render_template('concdiff.html')


@app.route('/catparse', methods=['POST', 'GET'])
def catparse_app():
    if request.method == 'POST':
        scribe_out = transcode(request.form['pasted'])
        return render_template('index.html',
                               scribe_out=scribe_out,
                               pasted=request.form['pasted'])
    else:
        return render_template('index.html')
