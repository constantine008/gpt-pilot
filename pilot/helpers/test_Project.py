import os
import json
import pytest
from unittest.mock import patch, MagicMock
from helpers.Project import Project
from database.models.files import File

test_root = os.path.join(os.path.dirname(__file__), '../../workspace/gpt-pilot-test').replace('\\', '/')


def create_project():
    project = Project({
        'app_id': 'test-project',
        'name': 'TestProject',
        'app_type': ''
    },
        name='TestProject',
        architecture=[],
        user_stories=[]
    )
    project.set_root_path(test_root)
    project.app = 'test'
    return project


@pytest.mark.parametrize('test_data', [
    {'name': 'package.json', 'path': 'package.json', 'saved_to': f'{test_root}/package.json'},
    {'name': 'package.json', 'path': '', 'saved_to': f'{test_root}/package.json'},
    # {'name': 'Dockerfile', 'path': None, 'saved_to': f'{test_root}/Dockerfile'},
    {'name': None, 'path': 'public/index.html', 'saved_to': f'{test_root}/public/index.html'},
    {'name': '', 'path': 'public/index.html', 'saved_to': f'{test_root}/public/index.html'},

    # TODO: Treatment of paths outside of the project workspace - https://github.com/Pythagora-io/gpt-pilot/issues/129
    # {'name': '/etc/hosts', 'path': None, 'saved_to': '/etc/hosts'},
    # {'name': '.gitconfig', 'path': '~', 'saved_to': '~/.gitconfig'},
    # {'name': '.gitconfig', 'path': '~/.gitconfig', 'saved_to': '~/.gitconfig'},
    # {'name': 'gpt-pilot.log', 'path': '/temp/gpt-pilot.log', 'saved_to': '/temp/gpt-pilot.log'},
], ids=[
    'name == path', 'empty path',
    # 'None path',
    'None name', 'empty name',
    # 'None path absolute file', 'home path', 'home path same name', 'absolute path with name'
])
@patch('helpers.Project.update_file')
@patch('helpers.Project.File')
def test_save_file(mock_file_insert, mock_update_file, test_data):
    # Given
    data = {'content': 'Hello World!'}
    if test_data['name'] is not None:
        data['name'] = test_data['name']
    if test_data['path'] is not None:
        data['path'] = test_data['path']

    project = create_project()

    # When
    project.save_file(data)

    # Then assert that update_file with the correct path
    expected_saved_to = test_data['saved_to']
    mock_update_file.assert_called_once_with(expected_saved_to, 'Hello World!')

    # Also assert that File.insert was called with the expected arguments
    # expected_file_data = {'app': project.app, 'path': test_data['path'], 'name': test_data['name'],
    #                       'full_path': expected_saved_to}
    # mock_file_insert.assert_called_once_with(app=project.app, **expected_file_data,
    #                                          **{'name': test_data['name'], 'path': test_data['path'],
    #                                             'full_path': expected_saved_to})


@pytest.mark.parametrize('file_path, file_name, expected', [
    ('file.txt', 'file.txt', f'{test_root}/file.txt'),
    ('', 'file.txt', f'{test_root}/file.txt'),
    ('path/', 'file.txt', f'{test_root}/path/file.txt'),
    ('path/to/', 'file.txt', f'{test_root}/path/to/file.txt'),
    ('path/to/file.txt', 'file.txt', f'{test_root}/path/to/file.txt'),
    ('./path/to/file.txt', 'file.txt', f'{test_root}/./path/to/file.txt'),  # ideally result would not have `./`
])
def test_get_full_path(file_path, file_name, expected):
    # Given
    project = create_project()

    # When
    relative_path, absolute_path = project.get_full_file_path(file_path, file_name)

    # Then
    assert absolute_path == expected


@pytest.mark.skip(reason="Handling of absolute paths will be revisited in #29")
@pytest.mark.parametrize('file_path, file_name, expected', [
    ('/file.txt', 'file.txt', '/file.txt'),
    ('/path/to/file.txt', 'file.txt', '/path/to/file.txt'),
    # Only passes on Windows? ('C:\\path\\to\\file.txt', 'file.txt', 'C:\\path\\to/file.txt'),
    ('~/path/to/file.txt', 'file.txt', '~/path/to/file.txt'),
])
def test_get_full_path_absolute(file_path, file_name, expected):
    # Given
    project = create_project()

    # When
    relative_path, absolute_path = project.get_full_file_path(file_path, file_name)

    # Then
    assert absolute_path == expected

# This is known to fail and should be avoided
# def test_get_full_file_path_error():
#     # Given
#     file_path = 'path/to/file/'
#     file_name = ''
#
#     # When
#     full_path = project.get_full_file_path(file_path, file_name)
#
#     # Then
#     assert full_path == f'{test_root}/path/to/file/'


class TestProjectFileLists:
    def setup_method(self):
        # Given a project
        project = create_project()
        self.project = project
        project.set_root_path(os.path.join(os.path.dirname(__file__), '../../workspace/directory_tree'))
        project.project_description = 'Test Project'
        project.development_plan = [{
            'description': 'Test User Story',
            'programmatic_goal': 'Test Programmatic Goal',
            'user_review_goal': 'Test User Review Goal',
        }]

        # with directories including common.IGNORE_FOLDERS
        src = os.path.join(project.root_path, 'src')
        foo = os.path.join(project.root_path, 'src/foo')
        files_no_folders = os.path.join(foo, 'files_no_folders')
        os.makedirs(src, exist_ok=True)
        os.makedirs(foo, exist_ok=True)
        os.makedirs(foo + '/empty1', exist_ok=True)
        os.makedirs(foo + '/empty2', exist_ok=True)
        os.makedirs(files_no_folders, exist_ok=True)
        for dir in ['.git', '.idea', '.vscode', '__pycache__', 'node_modules', 'venv', 'dist', 'build']:
            os.makedirs(os.path.join(project.root_path, dir), exist_ok=True)

        # ...and files

        with open(os.path.join(project.root_path, 'package.json'), 'w') as file:
            json.dump({'name': 'test app'}, file, indent=2)
        for path in [
            os.path.join(src, 'main.js'),
            os.path.join(src, 'other.js'),
            os.path.join(foo, 'bar.js'),
            os.path.join(foo, 'fighters.js'),
            os.path.join(files_no_folders, 'file1.js'),
            os.path.join(files_no_folders, 'file2.js'),
        ]:
            with open(path, 'w') as file:
                file.write('console.log("Hello World!");')

        # and a non-empty .gpt-pilot directory
        project.dot_pilot_gpt.write_project(project)

    def test_get_directory_tree(self):
        # When
        tree = self.project.get_directory_tree()

        # Then we should not be including the .gpt-pilot directory or other ignored directories
        # print('\n' + tree)
        assert tree == '''
/
  /src
    /foo
      /empty1
      /empty2
      /files_no_folders: file1.js, file2.js
      bar.js, fighters.js
    main.js, other.js
  package.json
'''.lstrip()

    @patch('helpers.Project.DevelopmentSteps.get_or_create', return_value=('test', True))
    @patch('helpers.Project.File.get_or_create', return_value=('test', True))
    @patch('helpers.Project.FileSnapshot.get_or_create', return_value=(MagicMock(), True))
    def test_save_files_snapshot(self, mock_snap, mock_file, mock_step):
        # Given a snapshot of the files in the project

        # When we save the file snapshot
        self.project.save_files_snapshot('test')

        # Then the files should be saved to the project, but nothing from `.gpt-pilot/`
        assert mock_file.call_count == 7
        files = ['package.json', 'main.js', 'file1.js', 'file2.js', 'bar.js', 'fighters.js', 'other.js']
        for i in range(7):
            assert mock_file.call_args_list[i][1]['name'] in files
