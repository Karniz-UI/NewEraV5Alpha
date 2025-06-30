#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import time
import psutil
import importlib
import importlib.util
import shutil
import logging
import aiohttp
import json
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import Message

# ==================== НАСТРОЙКА ЛОГГИРОВАНИЯ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("newera.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== ОСНОВНОЙ КЛАСС БОТА ====================
class NewEraV4Fix:
    def __init__(self):
        self.start_time = time.time()
        self.modules_dir = "modules"
        self.loaded_modules = {}
        self.module_commands = {}
        self.config = {}
        self.client = None
        self.session = aiohttp.ClientSession()
        
        # Стилизованные символы
        self.styled_chars = {
            'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ',
            'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
            'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ',
            'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ',
            'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ',
            'z': 'ᴢ', '0': '𝟢', '1': '𝟣', '2': '𝟤', '3': '𝟥',
            '4': '𝟦', '5': '𝟧', '6': '𝟨', '7': '𝟩', '8': '𝟪',
            '9': '𝟫'
        }
        
        # Локализация
        self.languages = {
            "ru": {
                "uptime": "Аптайм",
                "user": "Юзер", 
                "cpu": "Процессор",
                "ram": "Оперативка",
                "host": "Хост",
                "commands": "Команды",
                "help_text": """**NewEraV4Fix - команды:**

`.help` - Показать команды
`.info` - Информация о системе
`.ping` - Проверить пинг
`.lm` - Загрузить модуль (реплай на файл)
`.ulm <имя>` - Выгрузить модуль
`.modules` - Список модулей
`.logs` - Показать логи
`.setlang <ru/en>` - Сменить язык
`.restart` - Перезагрузка
`.stop` - Остановка
`.backup` - Создать бэкап
`.clean` - Очистить временные файлы""",
                "module_loaded": "✅ Модуль {} загружен",
                "module_unloaded": "✅ Модуль {} выгружен",
                "module_not_found": "❌ Модуль {} не найден",
                "lang_changed": "🌍 Язык изменен на {}",
                "restarting": "🔄 Перезагрузка...",
                "stopping": "🛑 Остановка...",
                "no_modules": "📦 Нет загруженных модулей",
                "modules_list": "📚 **Загруженные модули:**",
                "backup_created": "💾 Бэкап создан: {}",
                "temp_cleaned": "🧹 Очищено временных файлов: {}",
                "logs_empty": "🪵 Логов не найдено",
                "logs_title": "📜 Последние логи:",
                "logs_error": "❌ Ошибка чтения логов: {}",
                "ping_result": "⚡️Пинг: {}мс\n🌿 Бот активен",
                "ipinfo_result": """🔍 Информация о {}:
🌍 Страна: {}
🏙 Город: {}
📱 Провайдер: {}
📡 Организация: {}
📍 Координаты: {}, {}
⏰ Часовой пояс: {}""",
                "ipinfo_error": "❌ Ошибка запроса IP: {}",
                "file_not_found": "❌ Файл не найден",
                "not_reply": "❌ Это не ответ на сообщение",
                "not_py_file": "❌ Файл должен быть .py"
            },
            "en": {
                # Аналогичные переводы на английском
            }
        }

    # ==================== СИСТЕМНЫЕ МЕТОДЫ ====================
    def print_banner(self):
        banner = r"""
  _   _               _____           
 | \ | | _____      _| ____|_ __ __ _ 
 |  \| |/ _ \ \ /\ / /  _| | '__/ _` |
 | |\  |  __/\ V  V /| |___| | | (_| |
 |_| \_|\___| \_/\_/ |_____|_|  \__,_|

Build: #Fix7HxBy9x
Update: Not Updates
GoodLuck ♡
"""
        print(banner)

    def load_config(self):
        try:
            self.print_banner()
            print(" Удачи ".center(40, '—'))
            
            self.config = {
                "api_id": int(input("API ID: ").strip()),
                "api_hash": input("API Hash: ").strip(),
                "prefix": input("Префикс команд [.]: ").strip() or ".",
                "language": (input("Язык [ru/en]: ").strip() or "ru").lower(),
                "owner_id": input("ID владельца (опционально): ").strip() or None
            }
            
            print("=" * 40)
            return True
        except Exception as e:
            logger.critical(f"Config error: {e}")
            return False

    def get_text(self, key):
        return self.languages[self.config.get("language", "ru")].get(key, key)

    def get_uptime(self):
        uptime = int(time.time() - self.start_time)
        return f"{uptime // 3600:02d}:{(uptime % 3600) // 60:02d}:{uptime % 60:02d}"

    def get_system_info(self):
        try:
            memory = psutil.virtual_memory()
            return {
                "uptime": self.get_uptime(),
                "ram": f"{memory.percent:.1f}%"
            }
        except:
            return {
                "uptime": self.get_uptime(),
                "ram": "N/A"
            }

    def style_text(self, text):
        return ''.join([self.styled_chars.get(c.lower(), c) for c in text])

    # ==================== КОМАНДЫ БОТА ====================
    async def setup_handlers(self):
        prefix = self.config["prefix"]
        
        # Основные команды
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}help$"))
        async def help_handler(event):
            await event.edit(self.get_text("help_text"))
            
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}info$"))
        async def info_handler(event):
            info = self.get_system_info()
            me = await self.client.get_me()
            username = me.username or me.first_name
            
            text = f"""`╭─────────────────────
│     NewEraV4Fix     
├─────────────────────
│ {self.style_text('uptime')}: {info["uptime"]}      
│ {self.style_text('user')}: {username}       
│ {self.style_text('ram')}: {info["ram"]}           
│ {self.style_text('host')}: Termux         
╰─────────────────────
`"""
            await event.edit(text)
        
        # Ping/IPinfo
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}ping$"))
        async def ping_handler(event):
            start = time.time()
            msg = await event.edit("⚡️Пинг...")
            latency = round((time.time() - start) * 1000, 2)
            await msg.edit(self.get_text("ping_result").format(latency))
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}ipinfo (.+)$"))
        async def ipinfo_handler(event):
            ip = event.pattern_match.group(1)
            try:
                async with self.session.get(f"http://ip-api.com/json/{ip}") as resp:
                    data = await resp.json()
                    if data["status"] == "success":
                        result = self.get_text("ipinfo_result").format(
                            ip, data.get("country", "N/A"), data.get("city", "N/A"),
                            data.get("isp", "N/A"), data.get("org", "N/A"),
                            data.get("lat", ""), data.get("lon", ""),
                            data.get("timezone", "N/A")
                        )
                        await event.edit(result)
                    else:
                        await event.edit(self.get_text("ipinfo_error").format(data.get("message", "Unknown")))
            except Exception as e:
                await event.edit(self.get_text("ipinfo_error").format(str(e)))
                logger.error(f"IPInfo error: {e}", exc_info=True)
        
        # Логи
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}logs$"))
        async def logs_handler(event):
            try:
                if not os.path.exists("newera.log"):
                    await event.edit(self.get_text("logs_empty"))
                    return
                
                with open("newera.log", "r", encoding="utf-8") as f:
                    logs = f.readlines()[-20:]
                    await event.edit(f"{self.get_text('logs_title')}\n\n```{''.join(logs)}```")
            except Exception as e:
                await event.edit(self.get_text("logs_error").format(str(e)))
                logger.error(f"Logs error: {e}", exc_info=True)
        
        # Модули
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}lm$"))
        async def load_module_handler(event):
            if not event.is_reply:
                return await event.edit(self.get_text("not_reply"))
                
            reply = await event.get_reply_message()
            if not reply.document:
                return await event.edit(self.get_text("file_not_found"))
                
            file_name = reply.document.attributes[0].file_name
            if not file_name.endswith('.py'):
                return await event.edit(self.get_text("not_py_file"))
                
            module_name = file_name[:-3]
            await event.edit(f"⏳ Загрузка модуля {module_name}...")
            
            file_path = await reply.download_media()
            success = await self.load_module(file_path, module_name)
            
            text = self.get_text("module_loaded").format(module_name) if success else f"❌ Ошибка загрузки {module_name}"
            await event.edit(text)
            
            if os.path.exists(file_path):
                os.remove(file_path)
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}ulm (.+)$"))
        async def unload_module_handler(event):
            module_name = event.pattern_match.group(1)
            success = await self.unload_module(module_name)
            
            if success:
                await event.edit(self.get_text("module_unloaded").format(module_name))
            else:
                await event.edit(self.get_text("module_not_found").format(module_name))
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}modules$"))
        async def modules_handler(event):
            if not self.loaded_modules:
                return await event.edit(self.get_text("no_modules"))
                
            text = self.get_text("modules_list") + "\n"
            for name, module in self.loaded_modules.items():
                text += f"• `{name}`\n"
                if name in self.module_commands:
                    text += "  └ " + ", ".join(f"`{prefix}{cmd}`" for cmd in self.module_commands[name]) + "\n"
            await event.edit(text)
        
        # Системные команды
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}setlang (ru|en)$"))
        async def setlang_handler(event):
            lang = event.pattern_match.group(1)
            self.config["language"] = lang
            await event.edit(self.get_text("lang_changed").format(lang.upper()))
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}restart$"))
        async def restart_handler(event):
            await event.edit(self.get_text("restarting"))
            await self.client.disconnect()
            os.execl(sys.executable, sys.executable, *sys.argv)
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}stop$"))
        async def stop_handler(event):
            await event.edit(self.get_text("stopping"))
            await self.client.disconnect()
            sys.exit(0)
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}backup$"))
        async def backup_handler(event):
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.zip"
            
            try:
                shutil.make_archive(
                    os.path.join(backup_dir, f"backup_{timestamp}"),
                    'zip',
                    '.',
                    ['modules', 'main.py', 'newera.log']
                )
                await event.edit(self.get_text("backup_created").format(backup_name))
            except Exception as e:
                await event.edit(f"❌ Ошибка создания бэкапа: {str(e)}")
                logger.error(f"Backup error: {e}", exc_info=True)
        
        @self.client.on(events.NewMessage(outgoing=True, pattern=f"^\\{prefix}clean$"))
        async def clean_handler(event):
            try:
                temp_dir = "/tmp"
                count = 0
                if os.path.exists(temp_dir):
                    for filename in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                                count += 1
                        except Exception:
                            continue
                await event.edit(self.get_text("temp_cleaned").format(count))
            except Exception as e:
                await event.edit(f"❌ Ошибка очистки: {str(e)}")
                logger.error(f"Clean error: {e}", exc_info=True)

    # ==================== МЕТОДЫ МОДУЛЕЙ ====================
    async def load_module(self, file_path, module_name):
        try:
            os.makedirs(self.modules_dir, exist_ok=True)
            module_path = os.path.join(self.modules_dir, f"{module_name}.py")
            
            with open(file_path, "rb") as src, open(module_path, "wb") as dst:
                dst.write(src.read())
            
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "register"):
                handlers = await module.register(self.client)
                if hasattr(module, "commands"):
                    self.module_commands[module_name] = module.commands
                self.loaded_modules[module_name] = module
                logger.info(f"Module {module_name} loaded")
                return True
            return False
        except Exception as e:
            logger.error(f"Load module error: {e}", exc_info=True)
            return False

    async def unload_module(self, module_name):
        if module_name in self.loaded_modules:
            module = self.loaded_modules[module_name]
            if hasattr(module, "unregister"):
                await module.unregister(self.client)
            
            if module_name in self.module_commands:
                del self.module_commands[module_name]
            
            del self.loaded_modules[module_name]
            
            module_path = os.path.join(self.modules_dir, f"{module_name}.py")
            if os.path.exists(module_path):
                os.remove(module_path)
            
            logger.info(f"Module {module_name} unloaded")
            return True
        return False

    # ==================== ЗАПУСК БОТА ====================
    async def start(self):
        if not self.load_config():
            logger.critical("Failed to load config")
            return
            
        self.client = TelegramClient(
            "newera_session",
            self.config["api_id"],
            self.config["api_hash"]
        )
        
        try:
            await self.client.start()
            await self.setup_handlers()
            
            me = await self.client.get_me()
            logger.info(f"Bot started as @{me.username}")
            print(f"\nБот запущен как @{me.username}")
            print(f"Префикс команд: {self.config['prefix']}")
            print(f"Язык: {self.config['language']}")
            print("Используйте .help для списка команд\n")
            
            await self.client.run_until_disconnected()
        except Exception as e:
            logger.critical(f"Start error: {e}", exc_info=True)
        finally:
            await self.session.close()

# ==================== ТОЧКА ВХОДА ====================
if __name__ == "__main__":
    bot = NewEraV4Fix()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
