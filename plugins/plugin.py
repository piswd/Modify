""" PagerMaid module to manage plugins. """

import json
from re import search, I
from requests import get
from os import remove, rename, chdir, path, getcwd, makedirs
from os.path import exists, basename, isfile
from sys import exit
from shutil import copyfile, move
from glob import glob
from main import bot, reg_handler, des_handler, par_handler

working_dir = getcwd()


def move_plugin(file_path):
    file_path = file_path.replace(f'{working_dir}/', '')
    plugin_directory = f"{working_dir}/plugins/plugins/"
    if exists(f"{plugin_directory}{file_path}"):
        remove(f"{plugin_directory}{file_path}")
        move(file_path, plugin_directory)
    elif exists(f"{plugin_directory}{file_path}.disabled"):
        remove(f"{plugin_directory}{file_path}.disabled")
        move(file_path, f"{plugin_directory}{file_path}.disabled")
    else:
        move(file_path, plugin_directory)


def update_version(file_path, plugin_content, plugin_name, version):
    plugin_directory = f"{working_dir}/plugins/plugins/"
    with open(file_path, 'wb') as f:
        f.write(plugin_content)
    with open(f"{plugin_directory}version.json", 'r', encoding="utf-8") as f:
        version_json = json.load(f)
        version_json[plugin_name] = version
    with open(f"{plugin_directory}version.json", 'w') as f:
        json.dump(version_json, f)


def __list_plugins():
    plugin_paths = glob(f"{getcwd()}/plugins/plugins" + "/*.py")
    if not exists(f"{getcwd()}/plugins/plugins"):
        makedirs(f"{getcwd()}/plugins/plugins")
    result = [
        basename(file)[:-3]
        for file in plugin_paths
        if isfile(file) and file.endswith(".py") and not file.endswith("__init__.py")
    ]
    return result


async def upload_attachment(bot, file_path, chat_id, reply_id, caption=None):
    """ Uploads a local attachment file. """
    if not exists(file_path):
        return False
    try:
        await bot.send_document(
            chat_id,
            file_path,
            reply_to_message_id=reply_id,
            caption=caption
        )
    except BaseException as exception:
        raise exception
    return True


def check_plugin(name):
    active_plugin = sorted(__list_plugins())
    disabled_plugins = []
    chdir("plugins/plugins/")
    for target_plugin in glob(f"*.py.disabled"):
        disabled_plugins += [f"{target_plugin[:-12]}"]
    chdir(working_dir)
    if (name in active_plugin) and (not name in disabled_plugins):
        return True
    else:
        return False


def check_require(name, version):
    if check_plugin(name):
        plugin_directory = f"{working_dir}/plugins/plugins/"
        if exists(f"{plugin_directory}version.json"):
            with open(f"{plugin_directory}version.json", 'r', encoding="utf-8") as f:
                version_json = json.load(f)
            try:
                plugin_version = version_json[name]
            except:
                plugin_version = 9999999.0
        else:
            plugin_version = 9999999.0
        if plugin_version >= version or plugin_version == '0.0':
            return True, ''
        else:
            return False, f"???????????????**incoming** ???????????? (<{version})???" \
                          f"???????????? `{list(prefix_str)[0]}apt install incoming` ??????????????????????????????"
    else:
        return False, f"???????????????**incoming** ???????????????????????? `{list(prefix_str)[0]}apt install incoming` ??????????????????????????????"


active_plugins = sorted(__list_plugins())


async def plugin(message, args, origin_text):
    if len(message.text.split()) == 1:
        await message.edit("?????????????????? ~ ??????????????????")
        return
    reply = message.reply_to_message
    plugin_directory = f"{working_dir}/plugins/plugins/"
    if message.text.split()[1] == "install":
        if len(message.text.split()) == 2:
            await message.edit("??????????????? . . .")
            if reply:
                file_path = await bot.download_media(reply, file_name=f'{working_dir}/{reply.document.file_name}')
            else:
                file_path = await message.download_media(file_name=f'{working_dir}/{message.document.file_name}')
            if file_path is None or not file_path.endswith('.py'):
                await message.edit("?????????????????? ~ ????????????????????????????????????")
                try:
                    remove(str(file_path))
                except FileNotFoundError:
                    pass
                return
            move_plugin(file_path)
            await message.edit(f"?????? {path.basename(file_path)[:-3]} ????????????PagerMaid-Modify Beta ?????????????????????")
            exit()
        elif len(message.text.split()) >= 3:
            await message.edit("??????????????? . . .")
            success_list = []
            failed_list = []
            noneed_list = []
            for x in range(len(message.text.split()) - 2):
                plugin_name = message.text.split()[2 + x]
                plugin_online = \
                    json.loads(
                        get("https://raw.githubusercontent.com/xtaodada/PagerMaid_Plugins/beta/list.json").content)[
                        'list']
                if exists(f"{plugin_directory}version.json"):
                    with open(f"{plugin_directory}version.json", 'r', encoding="utf-8") as f:
                        version_json = json.load(f)
                    try:
                        plugin_version = version_json[plugin_name]
                    except:
                        plugin_version = False
                else:
                    temp_dict = {}
                    with open(f"{plugin_directory}version.json", 'w') as f:
                        json.dump(temp_dict, f)
                    plugin_version = False
                flag = False
                for i in plugin_online:
                    if i['name'] == plugin_name:
                        flag = True
                        if plugin_version:
                            if (float(i['version']) - float(plugin_version)) <= 0:
                                noneed_list.append(plugin_name)
                                break
                            else:
                                file_path = plugin_name + ".py"
                                plugin_content = get(
                                    f"https://raw.githubusercontent.com/xtaodada/PagerMaid_Plugins/beta/"
                                    f"{plugin_name}.py").content
                                update_version(file_path, plugin_content, plugin_name, i['version'])
                                move_plugin(file_path)
                                success_list.append(path.basename(file_path)[:-3])
                                break
                        else:
                            file_path = plugin_name + ".py"
                            plugin_content = get(
                                f"https://raw.githubusercontent.com/xtaodada/PagerMaid_Plugins/beta/"
                                f"{plugin_name}.py").content
                            update_version(file_path, plugin_content, plugin_name, i['version'])
                            move_plugin(file_path)
                            success_list.append(path.basename(file_path)[:-3])
                if not flag:
                    failed_list.append(plugin_name)
            msg = ""
            if len(success_list) > 0:
                msg += "???????????? : %s\n" % ", ".join(success_list)
            if len(failed_list) > 0:
                msg += "???????????? : %s\n" % ", ".join(failed_list)
            if len(noneed_list) > 0:
                msg += "???????????? : %s\n" % ", ".join(noneed_list)
            restart = len(success_list) > 0
            if restart:
                msg += "PagerMaid-Modify Beta ???????????????"
            await message.edit(msg)
            if restart:
                exit()
        else:
            await message.edit("?????????????????? ~ ??????????????????")
    elif message.text.split()[1] == "remove":
        if len(message.text.split()) == 3:
            if exists(f"{plugin_directory}{message.text.split()[2]}.py"):
                remove(f"{plugin_directory}{message.text.split()[2]}.py")
                try:
                    with open(f"{plugin_directory}version.json", 'r', encoding="utf-8") as f:
                        version_json = json.load(f)
                    version_json[message.text.split()[2]] = '0.0'
                    with open(f"{plugin_directory}version.json", 'w') as f:
                        json.dump(version_json, f)
                except:
                    pass
                await message.edit(f"?????????????????? {message.text.split()[2]}, PagerMaid-Modify Beta ?????????????????????")
                exit()
            elif exists(f"{plugin_directory}{message.text.split()[2]}.py.disabled"):
                remove(f"{plugin_directory}{message.text.split()[2]}.py.disabled")
                with open(f"{plugin_directory}version.json", 'r', encoding="utf-8") as f:
                    version_json = json.load(f)
                version_json[message.text.split()[2]] = '0.0'
                with open(f"{plugin_directory}version.json", 'w') as f:
                    json.dump(version_json, f)
                await message.edit(f"?????????????????? {message.text.split()[2]}.")
            elif "/" in message.text.split()[2]:
                await message.edit("?????????????????? ~ ??????????????????")
            else:
                await message.edit("?????????????????? ~ ???????????????????????????")
        else:
            await message.edit("?????????????????? ~ ??????????????????")
    elif message.text.split()[1] == "status":
        if len(message.text.split()) == 2:
            inactive_plugins = sorted(__list_plugins())
            disabled_plugins = []
            if not len(inactive_plugins) == 0:
                for target_plugin in active_plugins:
                    inactive_plugins.remove(target_plugin)
            chdir("plugins/plugins/")
            for target_plugin in glob(f"*.py.disabled"):
                disabled_plugins += [f"{target_plugin[:-12]}"]
            chdir(working_dir)
            active_plugins_string = ""
            inactive_plugins_string = ""
            disabled_plugins_string = ""
            for target_plugin in active_plugins:
                active_plugins_string += f"{target_plugin}, "
            active_plugins_string = active_plugins_string[:-2]
            for target_plugin in args:
                inactive_plugins_string += f"{target_plugin}, "
            inactive_plugins_string = inactive_plugins_string[:-2]
            for target_plugin in disabled_plugins:
                disabled_plugins_string += f"{target_plugin}, "
            disabled_plugins_string = disabled_plugins_string[:-2]
            if len(active_plugins) == 0:
                active_plugins_string = "`???????????????????????????`"
            if len(args) == 0:
                inactive_plugins_string = "`??????????????????????????????`"
            if len(disabled_plugins) == 0:
                disabled_plugins_string = "`?????????????????????`"
            output = f"**????????????**\n" \
                     f"?????????: {active_plugins_string}\n" \
                     f"?????????: {disabled_plugins_string}\n" \
                     f"????????????: {inactive_plugins_string}"
            await message.edit(output)
        else:
            await message.edit("?????????????????? ~ ??????????????????")
    elif message.text.split()[1] == "enable":
        if len(message.text.split()) == 3:
            if exists(f"{plugin_directory}{message.text.split()[2]}.py.disabled"):
                rename(f"{plugin_directory}{message.text.split()[2]}.py.disabled",
                       f"{plugin_directory}{message.text.split()[2]}.py")
                await message.edit(f"?????? {message.text.split()[2]} ????????????PagerMaid-Modify Beta ?????????????????????")
                exit()
            else:
                await message.edit("?????????????????? ~ ???????????????????????????")
        else:
            await message.edit("?????????????????? ~ ??????????????????")
    elif message.text.split()[1] == "disable":
        if len(message.text.split()) == 3:
            if exists(f"{plugin_directory}{message.text.split()[2]}.py") is True:
                rename(f"{plugin_directory}{message.text.split()[2]}.py",
                       f"{plugin_directory}{message.text.split()[2]}.py.disabled")
                await message.edit(f"?????? {message.text.split()[2]} ???????????????PagerMaid-Modify Beta ?????????????????????")
                exit()
            else:
                await message.edit("?????????????????? ~ ???????????????????????????")
        else:
            await message.edit("?????????????????? ~ ??????????????????")
    elif message.text.split()[1] == "upload":
        if len(message.text.split()) == 3:
            file_name = f"{message.text.split()[2]}.py"
            reply_id = None
            if reply:
                reply_id = reply.message_id
            if exists(f"{plugin_directory}{file_name}"):
                copyfile(f"{plugin_directory}{file_name}", file_name)
            elif exists(f"{plugin_directory}{file_name}.disabled"):
                copyfile(f"{plugin_directory}{file_name}.disabled", file_name)
            if exists(file_name):
                await message.edit("??????????????? . . .")
                await upload_attachment(bot, file_name, message.chat.id, reply_id,
                                        caption=f"PagerMaid-Modify {message.text.split()[2]} plugin.")
                remove(file_name)
                await message.delete()
            else:
                await message.edit("?????????????????? ~ ???????????????????????????")
        else:
            await message.edit("?????????????????? ~ ??????????????????")
    elif message.text.split()[1] == "update":
        unneed_update = "???????????????"
        need_update = "\n????????????"
        need_update_list = []
        if not exists(f"{plugin_directory}version.json"):
            await message.edit("???????????????????????????????????????")
            return
        with open(f"{plugin_directory}version.json", 'r', encoding="utf-8") as f:
            version_json = json.load(f)
        plugin_online = \
            json.loads(get("https://raw.githubusercontent.com/xtaodada/PagerMaid_Plugins/beta/list.json").content)[
                'list']
        for key, value in version_json.items():
            if value == "0.0":
                continue
            for i in plugin_online:
                if key == i['name']:
                    if (float(i['version']) - float(value)) <= 0:
                        unneed_update += "\n`" + key + "`???Ver  " + value
                    else:
                        need_update_list.extend([key])
                        need_update += "\n`" + key + "`???Ver  " + value + " --> Ver  " + i['version']
                    continue
        if unneed_update == "???????????????":
            unneed_update = ''
        if need_update == "\n????????????":
            need_update = ''
        if unneed_update == '' and need_update == '':
            await message.edit("??????????????????????????????")
        else:
            if len(need_update_list) == 0:
                await message.edit('??????????????????????????????...??????\n????????????????????????????????????...??????\n**??????????????????????????????**')
            else:
                print(6)
                await message.edit('??????????????????????????????...??????\n????????????????????????????????????...??????\n??????????????????...')
                plugin_directory = f"{working_dir}/plugins/plugins/"
                for i in need_update_list:
                    file_path = i + ".py"
                    plugin_content = get(
                        f"https://raw.githubusercontent.com/xtaodada/PagerMaid_Plugins/beta/{i}.py").content
                    with open(file_path, 'wb') as f:
                        f.write(plugin_content)
                    with open(f"{plugin_directory}version.json", 'r', encoding="utf-8") as f:
                        version_json = json.load(f)
                    for m in plugin_online:
                        if m['name'] == i:
                            version_json[i] = m['version']
                    with open(f"{plugin_directory}version.json", 'w') as f:
                        json.dump(version_json, f)
                    move_plugin(file_path)
                await message.edit('??????????????????????????????...??????\n????????????????????????????????????...??????\n' + need_update)
                await message.bot.disconnect()
    elif message.text.split()[1] == "search":
        if len(message.text.split()) == 2:
            await message.edit("??????????????????????????????")
        elif len(message.text.split()) == 3:
            search_result = []
            plugin_name = message.text.split()[2]
            plugin_online = \
                json.loads(
                    get("https://raw.githubusercontent.com/xtaodada/PagerMaid_Plugins/beta/list.json").content)[
                    'list']
            for i in plugin_online:
                if search(plugin_name, i['name'], I):
                    search_result.extend(['`' + i['name'] + '` / `' + i['version'] + '`\n  ' + i['des-short']])
            if len(search_result) == 0:
                await message.edit("?????????????????????????????????????????????")
            else:
                await message.edit('???????????????????????????????????????\n\n' + '\n\n'.join(search_result))
        else:
            await message.edit("?????????????????? ~ ??????????????????")
    elif message.text.split()[1] == "show":
        if len(message.text.split()) == 2:
            await message.edit("??????????????????????????????")
        elif len(message.text.split()) == 3:
            search_result = ''
            plugin_name = message.text.split()[2]
            plugin_online = \
                json.loads(
                    get("https://raw.githubusercontent.com/xtaodada/PagerMaid_Plugins/beta/list.json").content)[
                    'list']
            for i in plugin_online:
                if plugin_name == i['name']:
                    if i['supported']:
                        search_support = '???????????????'
                    else:
                        search_support = '?????????'
                    search_result = '????????????`' + i['name'] + '`\n?????????`Ver  ' + i['version'] + '`\n?????????`' + i[
                        'section'] + '`\n?????????`' + \
                                    i['maintainer'] + '`\n?????????`' + i['size'] + '`\n???????????????' + search_support + '\n?????????' + i[
                                        'des-short'] + '\n\n' + i['des']
                    break
            if search_result == '':
                await message.edit("?????????????????????????????????????????????")
            else:
                await message.edit(search_result)
    else:
        await message.edit("?????????????????? ~ ??????????????????")


reg_handler('apt', plugin)
des_handler('apt', '????????????????????? PagerMaid-Modify ????????????')
par_handler('apt', '{update|search|show|status|install|remove|enable|disable|upload} <????????????/??????>')
