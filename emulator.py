import argparse
import os
import sys
import tarfile

from fs_handler import VirtualFileSystem


class ShellEmulator:
    def __init__(self, fs_path):
        self.fs = VirtualFileSystem(fs_path)
        self.current_dir = '/'  # Начальная директория

    def prompt(self):
        return f"emulator:{self.current_dir}$ "

    def execute_command(self, command):
        if command == "ls":
            return self.ls()
        elif command.startswith("cd "):
            directory = command.split(" ", 1)[1]
            return self.cd(directory)
        elif command.startswith("chmod "):
            args = command.split(" ", 2)
            if len(args) != 3:
                return "Usage: chmod <permissions> <filename>"
            return self.chmod(args[1], args[2])
        elif command.startswith("rm "):
            filename = command.split(" ", 1)[1]
            return self.rm(filename)
        elif command.startswith("cat "):
            filename = command.split(" ", 1)[1]
            return self.cat(filename)
        elif command == "exit":
            sys.exit(0)
        else:
            return f"Unknown command: {command}"

    def ls(self):
        """
        Выводит содержимое текущей директории.
        """
        files = self.fs.list_files()

        # Определяем путь текущей директории
        # current_path = self.current_dir.lstrip('/') + '/' if self.current_dir != '/' else ''
        current_path = self.current_dir.lstrip('/') if self.current_dir != '/' else ''
        #print(current_path)
        #print(self.current_dir)
        #print(files)
        #print('end')

        if current_path != '':
            if current_path[-1] != '/':
                current_path += '/'

        # Фильтруем файлы текущей директории
        filtered_files = set()  # Используем множество для исключения дублирования
        for file in files:
            if file.startswith(current_path):
                relative_path = file[len(current_path):]
                top_level_item = relative_path.split('/')[0]  # Берём только верхний уровень
                filtered_files.add(top_level_item)

        # Возвращаем отсортированный список файлов/директорий
        return '\n'.join(sorted(filtered_files))

    # def ls(self):
    #     files = self.fs.list_files()
    #     # Фильтруем файлы текущей директории
    #     current_path = self.current_dir.lstrip('/') + '/' if self.current_dir != '/' else ''
    #     filtered_files = [f[len(current_path):].split('/')[0] for f in files if f.startswith(current_path)]
    #     # print(filtered_files)
    #     return '\n'.join(sorted(set(filtered_files)))

    # def ls(self):
    #     """
    #     Список файлов и директорий в текущей директории.
    #     """
    #     files = [name for name in self.fs.metadata if name.startswith(self.current_dir)]
    #     relative_files = [os.path.relpath(file, self.current_dir) for file in files]
    #     print("\n".join(relative_files))

    # def cd(self, directory):
    #     if directory == '/':
    #         self.current_dir = '/'
    #     elif directory == '..':
    #         self.current_dir = '/'.join(self.current_dir.rstrip('/').split('/')[:-1]) or '/'
    #     else:
    #         new_path = self.current_dir.rstrip('/') + '/' + directory if self.current_dir != '/' else '/' + directory
    #         print(directory)
    #         print(new_path)
    #         if any(f.startswith(new_path + '/') or f == new_path for f in self.fs.list_files()):
    #             self.current_dir = new_path
    #         else:
    #             return f"Directory not found: {directory}"
    #     return ""

    def cd(self, directory):
        """
        Переход в другую директорию (эмуляция), с учетом прав доступа.
        """
        if directory == '/':
            # Переход в корневую директорию
            self.current_dir = '/'
            return ""

        if directory == '..':
            # Переход в родительскую директорию
            if self.current_dir != '/':
                self.current_dir = '/'.join(self.current_dir.rstrip('/').split('/')[:-1]) or '/'
            return ""

        # # Формируем полный путь (учитывая абсолютные и относительные пути)
        # if directory.startswith('/'):  # Абсолютный путь
        #     possible_path = directory.rstrip('/')
        # else:  # Относительный путь
        #     possible_path = self.current_dir.rstrip('/') + '/' + directory

        if self.current_dir == '/' and len(self.current_dir) == 1:
            # print(self.current_dir)
            possible_path = self.current_dir.rstrip('/') + directory
        elif directory[0] == '/' and len(directory) != 1:
            possible_path = self.current_dir.rstrip('/')
            # print(self.current_dir)
            # print(directory[1:])
            possible_path = directory[1:]
        else:
            # print(self.current_dir)
            possible_path = self.current_dir.rstrip('/') + '/' + directory

        # Проверяем существование директории
        #print(possible_path)
        #print(self.fs.metadata)
        if possible_path not in self.fs.metadata or not self.fs.metadata[possible_path]["is_dir"]:
            return f"Directory not found or not a directory: {directory}, path - {possible_path}"

        # Проверяем права на выполнение для текущей директории
        if not self.fs.file_has_permission(possible_path, "execute"):
            return f"No permission to access directory: {directory}, path - {possible_path}"

        # Если все проверки пройдены, обновляем текущую директорию
        self.current_dir = possible_path
        return ""

    # def cd(self, directory):
    #     # Переход в другую директорию (эмуляция).
    #     if directory == '/':
    #         self.current_dir = '/'
    #     elif directory == '..':
    #         # Переход в родительскую директорию
    #         if self.current_dir != '/':
    #             self.current_dir = '/'.join(self.current_dir.rstrip('/').split('/')[:-1]) or '/'
    #     else:
    #         # Определяем полный путь (абсолютный или относительный)
    #         if self.current_dir == '/' and len(self.current_dir) == 1:
    #             # print(self.current_dir)
    #             possible_path = self.current_dir.rstrip('/') + directory
    #         elif directory[0] == '/' and len(directory) != 1:
    #             #  possible_path = self.current_dir.rstrip('/')
    #             # print(self.current_dir)
    #             # print(directory[1:])
    #             possible_path = directory[1:]
    #         else:
    #             # print(self.current_dir)
    #             possible_path = self.current_dir.rstrip('/') + '/' + directory
    #
    #         # Проверка, существует ли директория в виртуальной файловой системе
    #         if any(f.startswith(possible_path + '/') or f == possible_path for f in self.fs.list_files()):
    #             self.current_dir = possible_path
    #         else:
    #             return f"Directory not found: {directory}, path - {possible_path}"
    #     return ""

    def chmod(self, filename, new_permissions):
        """
        Изменяет права доступа к файлу.
        """
        if self.current_dir != '':
            if self.current_dir[-1] != '/':
                self.current_dir += '/'
        full_path = self.current_dir + filename + '/'
        #print(full_path)
        #print(self.fs.metadata)
        if full_path not in self.fs.metadata and full_path[-1] == '/':
            full_path = full_path[:-1]
            #print(full_path)
        if full_path not in self.fs.metadata:
            print(f"File '{filename}' not found.")
            return

        # Обновляем права
        self.fs.metadata[full_path]["permissions"] = new_permissions
        #print("new_permissions")
        #print(new_permissions)
        #print(self.fs.metadata[full_path]["permissions"])
        #print("new_permissions")
        print(f"Permissions for '{filename}' changed to '{new_permissions}'.")

    # def chmod(self, permissions, filename):
    #     full_path = self.current_dir.rstrip('/') + '/' + filename if self.current_dir != '/' else '/' + filename
    #     return self.fs.chmod_file(full_path, permissions)

    def rm(self, filename):
        """
        Удаляет файл или папку. Если это папка, удаляет её рекурсивно.
        """
        full_path = self.current_dir.rstrip('/') + '/' + filename if self.current_dir != '/' else '/' + filename
        #print(f"Removing '{full_path}'")
        #print(self.fs.metadata)
        if full_path not in self.fs.metadata and full_path[-1] == '/':
            full_path = full_path[:-1]
        elif full_path not in self.fs.metadata and full_path[-1] != '/':
            full_path += '/'

        # Проверка существования
        if full_path not in self.fs.metadata:
            return f"File or directory not found: {full_path}"

        # Проверка прав на запись
        if not self.fs.file_has_permission(full_path, "write"):
            return f"Permission denied: {filename}"

        # Если это директория
        if self.fs.metadata[full_path]["is_dir"]:
            if self.fs.file_has_permission(full_path, "write"):
                # Рекурсивно удаляем содержимое директории
                files_to_remove = [path for path in self.fs.metadata if path.startswith(full_path + '/')]
                #print("files_to_remove")
                #print(files_to_remove)
                #print("files_to_remove")
                for path in files_to_remove:
                    self.fs.remove_file(path)  # Удаляем из архива
                    del self.fs.metadata[path]  # Удаляем из метаданных

                return f"Directory '{filename}' and its contents successfully removed."
            else:
                return f"Permission for directory denied: {filename}"

        # Если это файл
        self.fs.remove_file(full_path)
        del self.fs.metadata[full_path]
        return f"File '{filename}' successfully removed."

    # def rm(self, filename):
    #     """
    #     Удаляет файл в текущей директории, если у пользователя есть права на запись.
    #     """
    #     # Формируем полный путь
    #     full_path = self.current_dir.rstrip('/') + '/' + filename if self.current_dir != '/' else '/' + filename
    #
    #     # Проверяем, существует ли файл
    #     if full_path not in self.fs.metadata:
    #         print(f"File not found: {filename}")
    #         return
    #
    #     # Проверяем права на запись
    #     if not self.fs.file_has_permission(full_path, "write"):
    #         print(f"Permission denied: {filename}")
    #         return
    #
    #     # Удаляем файл
    #     try:
    #         self.fs.remove_file(full_path)
    #         print(f"File '{filename}' successfully removed.")
    #     except Exception as e:
    #         print(f"Error while removing file '{filename}': {e}")

    # def rm(self, filename):
    #     full_path = self.current_dir + '/' + filename
    #     if not self.fs.file_has_permission(full_path, "write"):
    #         print(f"Permission denied: {filename}")
    #         return
    #     full_path = self.current_dir.rstrip('/') + '/' + filename if self.current_dir != '/' else '/' + filename
    #     return self.fs.remove_file(full_path)

    # def cat(self, filename):
    #     if not self.fs.file_has_permission(filename, "read"):
    #         print(f"Permission denied: {filename}")
    #         return
    #     full_path = self.current_dir.rstrip('/') + '/' + filename if self.current_dir != '/' else '/' + filename
    #     return self.fs.open_file(full_path)
    def cat(self, filename):
        """
        Выводит содержимое файла, если у пользователя есть права на чтение.
        """
        if self.current_dir != '':
            if self.current_dir[-1] == '/':
                self.current_dir = self.current_dir[:-1]
        full_path = self.current_dir + '/' + filename

        if not self.fs.file_has_permission(full_path, "read"):
            print(f"No permission to read '{filename}'.")
            return

        with tarfile.open(self.fs.tar_path, "r") as tar:
            try:
                file_obj = tar.extractfile(full_path)
                if file_obj:
                    # print(file_obj.read().decode("utf-8"))
                    return file_obj.read().decode("utf-8")
                else:
                    print(f"File '{filename}' is not a regular file.")
            except KeyError:
                print(f"File '{filename}' not found in the archive.")

    def run(self):
        while True:
            command = input(self.prompt())
            result = self.execute_command(command)
            if result:
                print(result)


def parse_args():
    parser = argparse.ArgumentParser(description="Shell emulator")
    parser.add_argument("fs_archive", help="Path to the tar archive of the virtual file system")
    return parser.parse_args()


def main():
    args = parse_args()
    emulator = ShellEmulator(args.fs_archive)
    emulator.run()


if __name__ == "__main__":
    main()
# python emulator.py test_fs.tar
# tar -cvf test_fs.tar testing