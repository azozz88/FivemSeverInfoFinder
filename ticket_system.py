import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
from datetime import datetime
from config import TICKET_CONFIG

class TicketView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label=TICKET_CONFIG['buttons']['create']['label'], 
                      emoji=TICKET_CONFIG['buttons']['create']['emoji'],
                      style=TICKET_CONFIG['buttons']['create']['style'], 
                      custom_id="create_ticket")
    async def create_ticket_button(self, interaction: discord.Interaction, button: Button):
        modal = TicketModal(self.bot)
        await interaction.response.send_modal(modal)

class TicketModal(discord.ui.Modal, title="فتح تذكرة دعم فني"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.cfx_code = discord.ui.TextInput(
            label="كود السيرفر",
            placeholder="cfx.re/join/xxxxxx",
            min_length=5,
            max_length=200,
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.cfx_code)

    async def on_submit(self, interaction: discord.Interaction):
        cfx_code = self.cfx_code.value
        if not 'cfx.re/join/' in cfx_code:
            await interaction.response.send_message(
                "❌ الرجاء إدخال رابط صحيح يبدأ بـ cfx.re/join/",
                ephemeral=True
            )
            return

        ticket_cog = self.bot.get_cog('TicketSystem')
        if ticket_cog:
            await interaction.response.defer()
            await ticket_cog.create_ticket(interaction, cfx_code)
        else:
            await interaction.response.send_message(
                "❌ حدث خطأ في نظام التذاكر",
                ephemeral=True
            )

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_tickets = {}

    @commands.command(name='setup_fivem')
    @commands.has_permissions(administrator=True)
    async def setup_fivem(self, ctx):
        """إعداد نظام التذاكر"""
        try:
            embed = discord.Embed(
                title="نظام الدعم الفني 🎫",
                description="للحصول على المساعدة في فحص سيرفر FiveM، اضغط على الزر أدناه لفتح تذكرة",
                color=TICKET_CONFIG['embed_color']
            )
            embed.add_field(
                name="📝 التعليمات",
                value="1. اضغط على زر 'فتح تذكرة'\n"
                      "2. أدخل رابط سيرفر FiveM المراد فحصه\n"
                      "3. انتظر رد فريق الدعم الفني",
                inline=False
            )
            embed.set_footer(text="شكراً لاستخدامك نظام التذاكر")

            view = TicketView(self.bot)
            await ctx.send("تم إعداد نظام التذاكر بنجاح!")  # رسالة تأكيد
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            await ctx.send(f"❌ حدث خطأ: {str(e)}")

    async def create_ticket(self, interaction, cfx_code):
        ticket_number = len(self.active_tickets) + 1
        ticket_name = f"{TICKET_CONFIG['prefix']}{interaction.user.name}-{ticket_number}"
        
        category = self.bot.get_channel(TICKET_CONFIG['category_id'])
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=False),  # المستخدم لا يمكنه الكتابة
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        for role_id in TICKET_CONFIG['staff_roles']:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await interaction.guild.create_text_channel(
            ticket_name,
            category=category,
            overwrites=overwrites
        )

        welcome_embed = discord.Embed(
            title="🎮 تذكرة فحص سيرفر FiveM",
            description=f"مرحباً {interaction.user.mention}!\nتم إنشاء تذكرة للتحقق من السيرفر: {cfx_code}",
            color=TICKET_CONFIG['embed_color']
        )
        welcome_embed.add_field(
            name="📝 التعليمات",
            value="1. اختر نوع الفحص من الأزرار أدناه\n2. انتظر نتائج الفحص\n3. يمكن للإدارة إغلاق التذكرة",
            inline=False
        )
        welcome_embed.set_footer(text=f"Ticket ID: {ticket_number}")

        class TicketControls(View):
            def __init__(self, bot):
                super().__init__(timeout=None)
                self.bot = bot
                self.cfx_code = cfx_code



            @discord.ui.button(label="استخراج معلومات السيرفر", style=discord.ButtonStyle.success, emoji="🔬", custom_id="full_scan")
            async def full_scan(self, i: discord.Interaction, button: Button):
                await i.response.defer()
                fivem_cog = self.bot.get_cog('FiveMScanner')
                if fivem_cog:
                    ctx = await self.bot.get_context(i.message)
                    await fivem_cog.fivem(ctx, cfx_code=self.cfx_code)
                else:
                    await i.followup.send("❌ حدث خطأ في نظام الفحص", ephemeral=True)

            @discord.ui.button(label="إغلاق التذكرة", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
            async def close_ticket(self, i: discord.Interaction, button: Button):
                if any(role.id in TICKET_CONFIG['staff_roles'] for role in i.user.roles):
                    await i.response.defer()
                    
                    # إنشاء embed للتأكيد
                    confirm_embed = discord.Embed(
                        title="🔒 تأكيد إغلاق التذكرة",
                        description="سيتم إغلاق التذكرة خلال 5 ثواني...",
                        color=discord.Color.red()
                    )
                    await i.followup.send(embed=confirm_embed)
                    
                    # تسجيل في قناة السجلات
                    log_channel = self.bot.get_channel(TICKET_CONFIG['log_channel_id'])
                    if log_channel:
                        ticket_cog = self.bot.get_cog('TicketSystem')
                        if ticket_cog and i.channel.id in ticket_cog.active_tickets:
                            ticket_info = ticket_cog.active_tickets[i.channel.id]
                            log_embed = discord.Embed(
                                title="🔒 تم إغلاق التذكرة",
                                description=f"تم إغلاق التذكرة بواسطة {i.user.mention}",
                                color=discord.Color.red()
                            )
                            log_embed.add_field(
                                name="معلومات التذكرة",
                                value=f"رقم التذكرة: {ticket_info['ticket_number']}\n"
                                      f"صاحب التذكرة: {ticket_info['author'].mention}\n"
                                      f"السيرفر: {ticket_info['cfx_code']}"
                            )
                            await log_channel.send(embed=log_embed)
                    
                    # انتظار 5 ثواني
                    await asyncio.sleep(5)
                    
                    # حذف الروم
                    try:
                        ticket_cog = self.bot.get_cog('TicketSystem')
                        if ticket_cog and i.channel.id in ticket_cog.active_tickets:
                            del ticket_cog.active_tickets[i.channel.id]
                        await i.channel.delete()
                    except discord.errors.NotFound:
                        pass  # الروم تم حذفه بالفعل
                    except Exception as e:
                        await i.followup.send(f"❌ حدث خطأ أثناء حذف الروم: {str(e)}", ephemeral=True)
                else:
                    await i.response.send_message("❌ فقط الإدارة يمكنها إغلاق التذكرة", ephemeral=True)

        controls = TicketControls(self.bot)
        await ticket_channel.send(
            content=f"{interaction.user.mention} {', '.join([f'<@&{role_id}>' for role_id in TICKET_CONFIG['staff_roles']])}",
            embed=welcome_embed,
            view=controls
        )
        
        self.active_tickets[ticket_channel.id] = {
            'author': interaction.user,
            'cfx_code': cfx_code,
            'created_at': datetime.now(),
            'ticket_number': ticket_number
        }

        success_embed = discord.Embed(
            title="✅ تم إنشاء التذكرة",
            description=f"تم إنشاء تذكرة جديدة في {ticket_channel.mention}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=success_embed, ephemeral=True)

        # تسجيل في قناة السجلات
        log_channel = self.bot.get_channel(TICKET_CONFIG['log_channel_id'])
        if log_channel:
            log_embed = discord.Embed(
                title="📝 تذكرة جديدة",
                description=f"تم إنشاء تذكرة جديدة بواسطة {interaction.user.mention}",
                color=TICKET_CONFIG['embed_color']
            )
            log_embed.add_field(name="السيرفر", value=cfx_code, inline=False)
            log_embed.add_field(name="رقم التذكرة", value=str(ticket_number), inline=False)
            await log_channel.send(embed=log_embed)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot)) 