#!/usr/bin/python

import MySQLdb as mysql


def file_contents(folder, paths):
    """
    Load database schemas from *.sql files
    """
    return map(lambda path: open('%s%s.sql' % (folder, path), 'r').read(), paths)


def commands(schemas):
    """
    Parse schemas passed in and returns contained commands
    """
    return reduce((lambda result, schema: result + schema.split('\n\n')), schemas, [])


def execute_operation(connection, operation):
    """
    Connects to database and execute SQL operation passed in
    """
    cursor = connection.cursor()
    cursor.execute(operation)


if __name__ == '__main__':
    folder = './data/norgate/'
    # TODO externalize the list (and then use 'norgate_data' script)
    schemas = [
        'continuous_back_adjusted',
        'continuous_spliced',
        'contract',
        'currency',
        'currency_pairs',
        'currencies',
        'market',
        'spot',
        'spot_market',
        'holidays',
        'exchange',
        'group',
        'delivery_month',
        'data_codes',
        'investment_universe'
    ]
    contents = commands(file_contents(folder, schemas))
    drop_commands = filter(lambda cmd: cmd.lower().startswith('drop'), contents)
    create_table_commands = filter(lambda cmd: cmd.lower().startswith('create table'), contents)
    connection = mysql.connect(host='localhost', user='sec_user', passwd='root', db='norgate')

    print '\n'.join(drop_commands)
    # execute_operation(connection, '\n'.join(drop_commands))
    # execute_operation(connection, '\n'.join(reversed(create_table_commands)))
