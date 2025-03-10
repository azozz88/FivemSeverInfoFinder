import discord
from discord.ext import commands
import requests
import json
from config import FIVEM_CONFIG, ERROR_MESSAGES, TICKET_CONFIG
import os

class FiveMScanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def fivem(self, ctx, *, cfx_code: str = None):
        # التحقق من أن الأمر ليس في DM
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ لا يمكن استخدام هذا الأمر في الرسائل الخاصة")
            return

        # التحقق من أن الأمر يستخدم فقط في التذاكر
        if not ctx.channel.name.startswith(TICKET_CONFIG['prefix']):
            await ctx.send("⚠️ يمكن استخدام هذا الأمر في التذاكر فقط")
            return

        try:
            # تنظيف وتحقق من صحة الكود
            cfx_code = cfx_code.strip()
            if 'cfx.re/join/' in cfx_code:
                server_code = cfx_code.split('cfx.re/join/')[-1].strip()
            else:
                await ctx.send(ERROR_MESSAGES['invalid_cfx'])
                return
            
            # الحصول على معلومات السيرفر
            api_url = FIVEM_CONFIG['api_url'].format(server_code=server_code)
            response = requests.get(
                api_url,
                headers=FIVEM_CONFIG['headers'],
                timeout=FIVEM_CONFIG['timeout_seconds']
            )
            
            # طباعة معلومات التشخيص كاملة
            print(f"Status Code: {response.status_code}")
            print(f"Full Response: {response.text}")  # طباعة الاستجابة كاملة
            

            # التحقق من حالة الاستجابة
            if response.status_code != 200:
                await ctx.send(ERROR_MESSAGES['server_not_found'])
                return
            
            data = response.json()
            server_data = data['Data']
            
            # حفظ الاستجابة الكاملة في ملف
            with open('server_info.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # إرسال الملف
            await ctx.send(file=discord.File('server_info.json'))
            
            # تجميع كل المتغيرات
            all_fields = []
            
            # إضافة المعلومات الأساسية
            emojis = FIVEM_CONFIG['emojis']
            all_fields.append((f"{emojis['players']} عدد اللاعبين", f"{server_data['clients']}/{server_data['sv_maxclients']}", True))
            all_fields.append((f"{emojis['ip']} IP", data.get('EndPoint', ''), True))
            
            # إضافة جميع المتغيرات من server_data
            for key, value in server_data.items():
                if isinstance(value, (str, int, bool)) and str(value).strip():
                    all_fields.append((f'🧨 {key}', str(value)[:1024], True))
            
            # إضافة جميع المتغيرات من vars
            if 'vars' in server_data:
                for key, value in server_data['vars'].items():
                    if str(value).strip():
                        emoji = '🔧'
                        if 'discord' in key.lower(): emoji = '🎮'
                        elif 'license' in key.lower(): emoji = '🔑'
                        elif 'banner' in key.lower(): emoji = '🖼️'
                        elif 'project' in key.lower(): emoji = '📝'
                        elif 'locale' in key.lower(): emoji = '🌍'
                        elif 'tag' in key.lower(): emoji = '🏷️'
                        
                        all_fields.append((f'{emoji} {key}', str(value)[:1024], True))
            
            # إضافة رابط الاتصال
            all_fields.append(('🔗 رابط الاتصال', f"connect {data['EndPoint']}", False))
            
            # تقسيم الحقول إلى مجموعات من 25
            field_groups = [all_fields[i:i + 24] for i in range(0, len(all_fields), 24)]
            
            # إنشاء وإرسال embeds متعددة
            for i, fields in enumerate(field_groups):
                embed = discord.Embed(
                    title=f"🎮 {server_data['hostname']}" if i == 0 else f"🎮 {server_data['hostname']} (تابع {i+1})",
                    color=FIVEM_CONFIG['embed_color']
                )
                
                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)
                
                await ctx.send(embed=embed)
            
            # إرسال الملف بعد الـ embeds
            await ctx.send("📁 معلومات السيرفر كاملة:", file=discord.File('server_info.json'))
            
            # تنظيف الملف بعد إرساله
            try:
                os.remove('server_info.json')
            except:
                pass

            # إعادة تفعيل الكتابة للمستخدم بعد إكمال الفحص
            if isinstance(ctx.channel, discord.TextChannel) and ctx.channel.name.startswith(TICKET_CONFIG['prefix']):
                await ctx.channel.set_permissions(ctx.author, send_messages=True)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            await ctx.send(ERROR_MESSAGES['general_error'])

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # التحقق من أن الرسالة ليست في DM
        if isinstance(message.channel, discord.DMChannel):
            return

        if 'cfx.re/join/' in message.content:
            ctx = await self.bot.get_context(message)
            await ctx.invoke(self.bot.get_command('fivem'), cfx_code=message.content.strip())

async def setup(bot):
    await bot.add_cog(FiveMScanner(bot))
