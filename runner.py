import datetime
import os
import shutil
import smtplib
import subprocess
import zipfile

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

repr_file = 'repr.txt'
png_file = 'optimized.png'
dat_file = 'optimized.dat'
log_file = 'log.txt'

sql_base_file = 'log.sql'
sql_zip_file = 'log.sql.zip'


def run(cl, n_c, n_t, b_c=8, b_t=8, b_te=8, gen=100,
        fix_te=True,
        constrain_thickness=True, constrain_area=True, constrain_moment=True,
        cm_ref=None, seed=None, n_proc=28,
        report=False,
        results_output_folder=None):
    """
    Solve the specified optimization problem and handle reporting of results.

    Parameters
    ----------
    cl : float
        Design lift coefficient
    n_c, n_t : int
        Number of CST coefficients for the chord line and thickness distribution, respectively
    b_c, b_t, b_te : int, optional
        Number of bits to encode each of the CST coefficients of the chord line/thickness distribution, and TE thickness
        8 bits each by default.
    gen : int, optional
        Number of generations to use for the genetic algorithm. 100 by default
    fix_te : bool, optional
        True if the trailing edge thickness should be fixed. True by default
    constrain_thickness, constrain_area, constrain_moment : bool, optional
        True if the thickness, area, and/or moment coefficient should be constrained, respectively. All True by default
    cm_ref : float, optional
        If constrain_moment is True, this will be the maximum (absolute) moment coefficient. If None, initial Cm is used
    seed : int, optional
        Seed to use for the random number generator which creates an initial population for the genetic algorithm
    n_proc : int, optional
        Number of processors to use to evaluate functions in parallel using MPI. 28 by default
    report : bool, optional
        True if the results should be reported via email.
    results_output_folder : str, optional
        Name of the shared folder in which to store results. By default, an ISO formatted UTC timestamp will be used.
    """
    try:
        cmd = ['mpirun', '-np', str(n_proc),
               'python3', 'problem.py',
               str(cl), str(n_c), str(n_t),
               str(b_c), str(b_t), str(b_te),
               str(gen), str(fix_te),
               str(constrain_thickness), str(constrain_area), str(constrain_moment),
               str(cm_ref), str(seed)]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout.decode('utf-8')
        print(output)

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(output)

        if results_output_folder is None:
            now = datetime.datetime.utcnow()
            results_output_folder = now.isoformat(timespec='seconds').replace('-', '').replace(':', '') + 'Z'

        with zipfile.ZipFile(sql_zip_file, 'w') as zf:
            for i in range(n_proc):
                zf.write(f'{sql_base_file}_{i}')

        path = os.path.join(os.path.abspath('share'), results_output_folder)
        os.mkdir(path)
        shutil.copy(repr_file, path)
        shutil.copy(png_file, path)
        shutil.copy(dat_file, path)
        shutil.copy(log_file, path)
        shutil.copy(sql_zip_file, path)

        if report:
            smtp_settings_file = os.environ['SMTP_SETTINGS']
            with open(smtp_settings_file, 'r') as f:
                smtp_settings = dict([line.strip().replace(' ', '').split('=') for line in f.readlines()])

            msg = MIMEMultipart()
            msg['From'] = smtp_settings['user']
            msg['To'] = smtp_settings['receiver']
            msg['Subject'] = 'Airfoil Optimization Complete!'
            with open(repr_file, 'r') as f:
                msg.attach(MIMEText(f.read(), 'plain'), )
            with open('optimized.png', 'rb') as fp:
                attachment = MIMEImage(fp.read(), _subtype='png')
                attachment.add_header('Content-Disposition', 'attachment', filename=png_file)
                msg.attach(attachment)
            with open(dat_file, 'r') as f:
                attachment = MIMEText(f.read())
                attachment.add_header('Content-Disposition', 'attachment', filename=dat_file)
                msg.attach(attachment)
            with open(log_file, 'r', encoding='utf-8') as f:
                attachment = MIMEText(f.read())
                attachment.add_header('Content-Disposition', 'attachment', filename=log_file)
                msg.attach(attachment)

            with smtplib.SMTP_SSL(smtp_settings['host'], int(smtp_settings['port'])) as server:
                server.ehlo()
                server.login(smtp_settings['user'], smtp_settings['password'])
                server.sendmail(smtp_settings['user'], smtp_settings['receiver'], msg.as_string())
                print('Email sent')
    except Exception as e:
        print(e)


def main():
    """
    Run all optimization problems defined in the Runfile.
    """
    with open('Runfile', 'r') as f:
        eval(f'run({f.readline()})')


if __name__ == '__main__':
    main()
