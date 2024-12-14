import tarfile
import os
from stat import S_IMODE, S_IRUSR, S_IWUSR, S_IXUSR, S_IRGRP, S_IWGRP, S_IXGRP, S_IROTH, S_IWOTH, S_IXOTH


class VirtualFileSystem:
    def __init__(self, tar_path):
        self.tar_path = tar_path
        self.metadata = {}  # Метаданные файлов
        self._load_metadata()

    def remove_file(self, full_path):
        """
        Удаляет файл или папку из архива.
        """
        #print(full_path + "PATH")
        if full_path[-1] == '/':
            full_path = full_path[:-1]
        with tarfile.open(self.tar_path, "r") as tar:
            if full_path not in tar.getnames():
                #print(tar.getnames())
                raise FileNotFoundError(f"File or directory '{full_path}' does not exist.")

        temp_tar_path = self.tar_path + ".tmp"
        with tarfile.open(self.tar_path, "r") as tar, tarfile.open(temp_tar_path, "w") as new_tar:
            for member in tar.getmembers():
                if member.name == full_path or member.name.startswith(full_path + "/"):
                    continue  # Пропускаем удаляемые файлы и папки
                file_obj = tar.extractfile(member)
                if file_obj:
                    new_tar.addfile(member, file_obj)
                else:
                    new_tar.addfile(member)

        os.replace(temp_tar_path, self.tar_path)

    # def remove_file(self, full_path):
    #     """
    #     Удаляет файл, если разрешение позволяет это сделать.
    #     """
    #     if not self.file_has_permission(full_path, "write"):
    #         raise PermissionError(f"No permission to remove '{full_path}'.")
    #
    #     with tarfile.open(self.tar_path, "r") as tar:
    #         if full_path not in tar.getnames():
    #             raise FileNotFoundError(f"File '{full_path}' does not exist.")
    #
    #     # Создаём временный архив
    #     temp_tar_path = self.tar_path + ".tmp"
    #
    #     with tarfile.open(self.tar_path, "r") as tar, tarfile.open(temp_tar_path, "w") as new_tar:
    #         for member in tar.getmembers():
    #             if member.name == full_path:
    #                 continue  # Пропускаем файл, который нужно удалить
    #             file_obj = tar.extractfile(member)
    #             if file_obj:
    #                 new_tar.addfile(member, file_obj)
    #             else:
    #                 new_tar.addfile(member)
    #
    #     os.replace(temp_tar_path, self.tar_path)
    #     del self.metadata[full_path]
    #     print(f"File '{full_path}' successfully removed.")

    def remove_duplicate_dirs(self):
        updated_metadata = {}

        for key, value in self.metadata.items():
            # Определяем базовое имя директории
            normalized_key = key.rstrip('/')
            if normalized_key in updated_metadata:
                # Если дубликат уже добавлен, сравниваем права доступа и оставляем более строгие
                existing_perms = updated_metadata[normalized_key]['permissions']
                current_perms = value['permissions']
                if existing_perms > current_perms:  # Строгость прав
                    continue
            updated_metadata[normalized_key] = value

        return updated_metadata

    def _load_metadata(self):
        """
        Загружает метаданные файлов и директорий из TAR.
        """
        with tarfile.open(self.tar_path, "r") as tar:
            directories = set()
            for member in tar.getmembers():
                # Обработка файла
                permissions = self._decode_permissions(member.mode)
                self.metadata[member.name] = {
                    "permissions": permissions,
                    "owner": member.uname or "root",
                    "group": member.gname or "root",
                    "is_dir": member.isdir(),
                }

                # Сохраняем все родительские директории
                path_parts = member.name.split('/')
                for i in range(1, len(path_parts)):
                    directories.add('/'.join(path_parts[:i]) + '/')

            # Добавляем директории в метаданные
            for directory in directories:
                if directory not in self.metadata:
                    self.metadata[directory] = {
                        "permissions": "rwxr-xr-x",  # Стандартные права для папок
                        "owner": "root",
                        "group": "root",
                        "is_dir": True,
                    }
            self.metadata = self.remove_duplicate_dirs()

    # def _load_metadata(self):
    #     """
    #     Загружает метаданные файлов из TAR.
    #     """
    #     with tarfile.open(self.tar_path, "r") as tar:
    #         for member in tar.getmembers():
    #             # Декодируем права доступа
    #             permissions = self._decode_permissions(member.mode)
    #             self.metadata[member.name] = {
    #                 "permissions": permissions,
    #                 "owner": member.uname or "root",
    #                 "group": member.gname or "root",
    #                 "is_dir": member.isdir()
    #             }

    def _decode_permissions(self, mode):
        """
        Преобразует число прав доступа (mode) в строку rwxrwxrwx.
        """
        flags = [
            S_IRUSR, S_IWUSR, S_IXUSR,
            S_IRGRP, S_IWGRP, S_IXGRP,
            S_IROTH, S_IWOTH, S_IXOTH
        ]
        chars = ["r", "w", "x"]
        perms = []
        for flag in flags:
            perms.append(chars[flags.index(flag) % 3] if mode & flag else "-")
        return "".join(perms)

    # def file_has_permission(self, filename, operation, user="user"):
    #     """
    #     Проверяет, имеет ли пользователь право на операцию (read, write, execute).
    #     """
    #     if filename not in self.metadata:
    #         raise FileNotFoundError(f"File '{filename}' does not exist.")
    #
    #     file_metadata = self.metadata[filename]
    #     permissions = file_metadata["permissions"]
    #
    #     user_roles = {"user": 0, "group": 1, "other": 2}
    #     role = user_roles.get(user, 2)  # Если роль не определена, считать "другие"
    #     offsets = {"read": 0, "write": 1, "execute": 2}
    #
    #     # Позиция в строке rwxrwxrwx
    #     pos = role * 3 + offsets[operation]
    #     return permissions[pos] != "-"
    def file_has_permission(self, filename, operation, user="user"):
        """
        Проверяет, имеет ли пользователь право на операцию (read, write, execute).
        """
        # Построим полный путь
        full_path = filename

        if full_path not in self.metadata:
            print(f"File '{full_path}' does not exist.")

        file_metadata = self.metadata[full_path]
        permissions = file_metadata["permissions"]

        # print(permissions)

        user_roles = {"user": 0, "group": 1, "other": 2}
        role = user_roles.get(user, 2)  # Если роль не определена, считать "другие"
        offsets = {"read": 0, "write": 1, "execute": 2}

        if permissions[0] in '0123456789' and permissions[1] in '0123456789' and permissions[2] in '0123456789':
            new_permissions = ""
            for i in range(3):
                if permissions[i] == '4':
                    new_permissions += 'r--'
                elif permissions[i] == '5':
                    new_permissions += 'r-x'
                elif permissions[i] == '6':
                    new_permissions += 'rw-'
                elif permissions[i] == '7':
                    new_permissions += 'rwx'
                elif permissions[i] == '1':
                    new_permissions += '--x'
                elif permissions[i] == '2':
                    new_permissions += '-w-'
                elif permissions[i] == '3':
                    new_permissions += '-wx'
                else:
                    new_permissions += '---'

            permissions = new_permissions

        #(permissions)
        # Позиция в строке rwxrwxrwx
        pos = role * 3 + offsets[operation]
        #print(pos)
        #print(permissions[pos])

        if permissions[pos] == "-":
            return False

        # Дополнительно проверяем, что если это папка, права применимы корректно
        if file_metadata["is_dir"] and operation in {"read", "write", "execute"}:
            #print(permissions[pos] != "-")
            return permissions[pos] != "-"

        return permissions[pos] != "-"

    # def file_has_permission(self, filename, operation, user="user"):
    #     """
    #     Проверяет, имеет ли пользователь право на операцию (read, write, execute).
    #     """
    #     # Построим полный путь
    #     full_path = filename
    #
    #     print(self.metadata)
    #     if full_path not in self.metadata:
    #         raise FileNotFoundError(f"File '{full_path}' does not exist.")
    #
    #     file_metadata = self.metadata[full_path]
    #     permissions = file_metadata["permissions"]
    #
    #     user_roles = {"user": 0, "group": 1, "other": 2}
    #     role = user_roles.get(user, 2)  # Если роль не определена, считать "другие"
    #     offsets = {"read": 0, "write": 1, "execute": 2}
    #     #print(role)
    #
    #     new_permissions = ""
    #     for i in range(3):
    #         if permissions[i] == '4':
    #             new_permissions += 'r--'
    #         elif permissions[i] == '5':
    #             new_permissions += 'r-e'
    #         elif permissions[i] == '6':
    #             new_permissions += 'rw-'
    #         elif permissions[i] == '7':
    #             new_permissions += 'rwe'
    #         elif permissions[i] == '1':
    #             new_permissions += '--e'
    #         elif permissions[i] == '2':
    #             new_permissions += '-w-'
    #         elif permissions[i] == '3':
    #             new_permissions += '-we'
    #         else:
    #             new_permissions += '---'
    #
    #     permissions = new_permissions
    #     # Позиция в строке rwxrwxrwx
    #     pos = role * 3 + offsets[operation]
    #     #print(pos)
    #     #print(permissions[pos])
    #     return permissions[pos] != "-"

    def list_files(self):
        with tarfile.open(self.tar_path, 'r') as tar:
            return tar.getnames()

    def open_file(self, filename):
        with tarfile.open(self.tar_path, 'r') as tar:
            try:
                file = tar.extractfile(filename)
                return file.read().decode('utf-16') if file else f"File not found: {filename}"
            except KeyError:
                return f"File not found: {filename}"

    def chmod_file(self, filename, permissions):
        # Обновление прав доступа для файла
        with tarfile.open(self.tar_path, 'r') as tar:
            try:
                file_info = tar.getmember(filename)
                file_info.mode = int(permissions, 8)
                return f"Permissions for '{filename}' updated to {permissions}"
            except KeyError:
                return f"File not found: {filename}"

    # def remove_file(self, filename):
    #     # Удаление файла из архива
    #     with tarfile.open(self.tar_path, 'r') as tar:
    #         try:
    #             members = tar.getmembers()
    #             updated_members = [m for m in members if m.name != filename]
    #
    #             # Создание нового архива
    #             with tarfile.open(self.tar_path, 'w') as new_tar:
    #                 for member in updated_members:
    #                     new_tar.addfile(member, tar.extractfile(member.name))
    #             return f"File '{filename}' removed."
    #         except KeyError:
    #             return f"File not found: {filename}"
