import uuid
from difflib import HtmlDiff
from subprocess import Popen, PIPE
from opster import command

from flask import Flask, redirect
from flaskext.cache import Cache
from jinja2 import Template


app = Flask(__name__)
app.config['TESTING'] = False
app.config['CACHE_TYPE'] = 'memcached'
app.config['CACHE_MEMCACHED_SERVERS'] = ['127.0.0.1:11211']
cache = Cache()
cache.init_app(app)

TOKEN_NO_FILE = str(uuid.uuid4())
TOKEN_NO_SERVER = str(uuid.uuid4())


def get_watch_data(diff_servers, diff_files):
    """Retrieve the contents of the files in diff_files from the servers in diff_servers.

    :param diff_servers: A list of host names where to look for the files. 
    :param diff_files: A list of filenames to retrieve.
    :returns: A dictionary of {diff_server: {diff_file: contents}}

    """
    username = app.config.get('SSH_USERNAME')
    watch_data = dict()
    for server in diff_servers:
        watch_data[server] = dict()
        for filename in diff_files:
            output = Popen("ssh {user_at}{server} 'sudo cat \"{filename}\" || echo {token_no_file}' || echo {token_no_server}"
                    .format(user_at = username + '@' if username else '', server=server, filename=filename,
                            token_no_file=TOKEN_NO_FILE, token_no_server=TOKEN_NO_SERVER), stdout=PIPE,
                            shell=True).communicate()[0]
            if output.strip() not in [TOKEN_NO_FILE, TOKEN_NO_SERVER]:
                watch_data[server][filename] = output
    return watch_data


def get_diff_groups(diff_servers, diff_files, watch_data):
    """For every file, group together the servers that have the exact same version of the file.

    :param diff_servers: A list of host names where to look for the files. 
    :param diff_files: A list of files to retrieve.
    :param watch_data: A dictionary of {diff_server: {diff_file: contents}}
    :returns: A dictionary of {diff_file: [file_contents, diff_servers]} grouping together, for each filename in
       diff_files, the servers in diff_servers where the contents of the file is the same.

    """
    diff_groups = dict() # file: [[contents, diff group]]
    for filename in diff_files: 
        groups = []
        dont_have_file = []
        for server in diff_servers:
            if filename not in watch_data[server]:
                dont_have_file.append(server)
            else:
                def has_equal_file(filename, contents, servers):
                    for f in servers:
                        if watch_data[f][filename] == contents:
                            return True
                    return False
                contents = watch_data[server][filename]
                has_group = False
                for group in groups:
                    if has_equal_file(filename, contents, group):
                        group.append(server)
                        has_group = True
                        break
                if not has_group:
                    groups.append([server])
        diff_groups[filename] = [[None, dont_have_file]] + [[watch_data[g[0]][filename], g] for g in groups]
    return diff_groups


@app.route("/")
@cache.cached(key_prefix='diffs_view')
def all_diffs():
    """Generate the HTML diffs and render them in the template.

    """

    file_diffs = []
    diff_servers = app.config['DIFF_SERVERS']
    diff_files = app.config['DIFF_FILES']
    watch_data = get_watch_data(diff_servers, diff_files)
    grouped_data = get_diff_groups(diff_servers, diff_files, watch_data)
    for filename in diff_files: 
        diff_groups = grouped_data[filename]
        dont_have = None
        last_contents = None
        servers_diffs = []
        last_group = None
        for contents, group in diff_groups:
            if contents is None:
                dont_have = ', '.join(group)
                continue
            if last_contents is not None:
                diff = HtmlDiff().make_table(last_contents.split('\n'), contents.split('\n'), ':'.join(
                    (last_group, filename)), ':'.join((','.join(group),filename)))
                servers_diffs += [{'servers': ', '.join(group), 'diff': diff}]
            else:
                servers_diffs += [{'servers': ', '.join(group), 'diff': '<pre>{0}</pre>'.format(contents)}]
            last_contents = contents
            last_group = ','.join(group)
        if dont_have:
            servers_diffs.append({'servers': dont_have})
        file_diffs.append({'file': filename, 'diffs': servers_diffs})
    idx = 1
    for f in file_diffs:
        for fd in f['diffs']:
            fd['idx'] = idx
            idx += 1
    return Template(DIFFS_TEMPLATE).render(file_diffs=file_diffs)


@app.route("/refresh")
def refresh():
    """Delete the cache and refresh the page.

    """

    cache.delete('diffs_view')
    return redirect('/')


@command(usage='-f FILES -s SERVERS [-p PORT] [-u|--username USERNAME] [-d|--debug]')
def run(files=('f', '', 'Files to compare, comma-separated'),
        servers=('s', '', 'Servers to compare, comma-separated'),
        port=('p', 5000, 'Port to listen to'),
        username=('u','', 'ssh username (default: use the current user)'),
        debug=('d', False, 'Debug mode')):
    """Starts an HTTP server that shows the differences between the specified files in the specified servers.
    """
    if not files:
        raise Exception("Specify at least one file")
    if not servers:
        raise Exception("Specify at least one server")
    print 'Starting the application on port {0}'.format(port)
    app.config['DIFF_FILES'] = map(str.strip, files.split(','))
    app.config['DIFF_SERVERS'] = map(str.strip, servers.split(','))
    if username:
        app.config['SSH_USERNAME'] = username
    
    app.run(port=port, debug=False)


DIFFS_TEMPLATE = """
<html>
    <head>
        <title>Diff my servers!</title>
        <link rel="stylesheet" href="http://ajax.microsoft.com/ajax/jquery.ui/1.8.5/themes/sunny/jquery-ui.css" type="text/css"/>
        <style type="text/css">
            table.diff {font-family:Courier,Mono; border:medium;}
            .diff_header {background-color:#e0e0e0}
            td.diff_header {text-align:right}
            .diff_next {background-color:#c0c0c0}
            .diff_add {background-color:#aaffaa}
            .diff_chg {background-color:#ffff77}
            .diff_sub {background-color:#ffaaaa}
            table.diff {width: 100%}
            pre {font-family:Courier,Mono}
            h3 {
                font-size: 0.5em
            }
            div.tabs {
                height: 600px;
            }
            body {
                font-size: 0.8em;
            }
        </style>
    </head>
    <body>
        <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.5.1/jquery.min.js"></script>
        <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.5/jquery-ui.min.js"></script>

        <script>
	$(function() {
        $( "#accordion" ).accordion();
		$( ".tabs" ).tabs();
	});
	</script>
    <h1 style="float:left">Diff My Servers!</h1>
    <div style="float:right"><a href="/refresh"><img src="http://i.imgur.com/KFruq.png"/></a></div>
    <div style="clear:both"></div>
        <div id="accordion">
            {% for file_diff in file_diffs %}
            <h3><a href="#">{% if file_diff.diffs|length() == 1 %}<em>{{ file_diff.file }}</em>{% else %}{{ file_diff.file }}{% endif %}</a></h3>
            <div class="tabs">
                <ul>
                    {% for diff in file_diff.diffs %}
                    <li><a href="#tabs-{{ diff.idx }}">
                        {% if diff.diff %}
                        {{ diff.servers }}
                        {% else %}
                        <em>{{ diff.servers }}</em>
                        {% endif %}
                    </a></li>
                    {% endfor %}
                </ul>
                {% for diff in file_diff.diffs %}
                <div id="tabs-{{ diff.idx }}">
                    {% if diff.diff %}
                    {{ diff.diff|safe }}
                    {% else %}
                    <p>File not found.</p>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </div>
    </body>
</html>
"""

