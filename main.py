import os
import json
import uuid
from pathlib import Path
import flet as ft

try:
    BASE_DIR = Path(__file__).parent
except NameError:
    BASE_DIR = Path.cwd()

DATA_FILE = BASE_DIR / "campaign_os_data.json"


def main(page: ft.Page):
    page.title = "Campaign OS"
    page.favicon = "icon2.png"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0b1020"
    page.window_width = 430
    page.window_height = 850
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    current_view = {"screen": "start"}
    latest_campaign = {"data": None}
    editing_campaign_id = {"value": None}
    editing_note_id = {"value": None}

    campaigns = []
    notes = []
    settings_state = {
        "glow_intensity": 34,
        "card_radius": 28,
    }

    form_state = {
        "campaign_name": "",
        "campaign_mode": "Digital",
        "channel": "Social Media",
        "campaign_type": "Branding",
        "budget": "1000",
        "estimated_traffic": "10000",
        "estimated_offline_reach": "50000",
        "website_conversion_rate": "2.5",
        "campaign_duration_days": "7",
        "average_purchase_value": "50",
        "estimated_purchase_value_uplift": "0",
        "baseline_daily_store_traffic": "1000",
        "estimated_traffic_uplift": "10",
    }

    note_form_state = {
        "title": "",
        "content": "",
    }

    # -----------------------------
    # Persistence
    # -----------------------------
    def save_app_data():
        payload = {
            "campaigns": campaigns,
            "notes": notes,
            "settings": settings_state,
        }
        try:
            DATA_FILE.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as ex:
            show_snackbar(f"Save error: {ex}")

    def load_app_data():
        nonlocal campaigns, notes

        if not DATA_FILE.exists():
            return

        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            campaigns = data.get("campaigns", [])

            # Ensure legacy campaigns have unique ids so library actions work.
            for campaign in campaigns:
                if "id" not in campaign or not campaign.get("id"):
                    campaign["id"] = str(uuid.uuid4())

            loaded_notes = data.get("notes", None)

            # backward compatibility with old single notes_text
            if isinstance(loaded_notes, list):
                notes = loaded_notes
            else:
                old_note_text = data.get("notes_text", "")
                if old_note_text.strip():
                    notes = [
                        {
                            "id": str(uuid.uuid4()),
                            "title": "Campaign Notes",
                            "content": old_note_text,
                        }
                    ]
                else:
                    notes = []

            loaded_settings = data.get("settings", {})
            settings_state["glow_intensity"] = int(
                loaded_settings.get("glow_intensity", 34)
            )
            settings_state["card_radius"] = int(
                loaded_settings.get("card_radius", 28)
            )
        except Exception:
            campaigns = []
            notes = []

    # -----------------------------
    # Theme tokens
    # -----------------------------
    def colors():
        is_light = page.theme_mode == ft.ThemeMode.LIGHT
        return {
            "is_light": is_light,
            "page_bg": "#eef2ff" if is_light else "#0b1020",
            "surface": "#ffffff" if is_light else "#101933",
            "surface_2": "#dbeafe" if is_light else "#16213a",
            "surface_3": "#c7d2fe" if is_light else "#1e293b",
            "border": "#c7d2fe" if is_light else "#2b3e6f",
            "text": "#0f172a" if is_light else "white",
            "text_2": "#475569" if is_light else "#cbd5e1",
            "text_3": "#64748b" if is_light else "#94a3b8",
            "primary": "#4f46e5",
            "primary_2": "#2563eb",
            "glow": "#2563eb",
            "success": "#16a34a",
            "warning": "#f59e0b",
            "danger": "#dc2626",
            "muted_btn": "#334155" if not is_light else "#cbd5e1",
            "field_bg": "#0b1220" if not is_light else "#ffffff",
            "icon_btn_bg": "#1a2340" if not is_light else "#dbeafe",
            "selected_btn": "#6366f1",
            "unselected_btn": "#334155" if not is_light else "#cbd5e1",
        }

    def glow_shadow(strength=None, color=None):
        c = colors()
        actual_strength = (
            settings_state["glow_intensity"] if strength is None else strength
        )
        return ft.BoxShadow(
            blur_radius=actual_strength,
            color=color or c["glow"],
            offset=ft.Offset(0, 8),
        )

    def soft_card_shadow():
        c = colors()
        return ft.BoxShadow(
            blur_radius=18,
            color="#1d4ed8" if not c["is_light"] else "#93c5fd",
            offset=ft.Offset(0, 6),
        )

    # -----------------------------
    # Helpers
    # -----------------------------
    def to_float(value, default=0.0):
        try:
            return float(str(value).replace(",", "."))
        except Exception:
            return default

    def to_int(value, default=0):
        try:
            return int(float(str(value).replace(",", ".")))
        except Exception:
            return default

    def calculate_campaign_metrics(
        channel: str,
        budget: float,
        estimated_traffic: int,
        website_conversion_rate: float,
        estimated_offline_reach: int,
        campaign_duration_days: int,
        average_purchase_value: float,
        estimated_purchase_value_uplift: float,
        baseline_daily_store_traffic: int,
        estimated_traffic_uplift: float,
    ):
        is_offline = channel == "Offline"

        if not is_offline:
            digital_revenue = (
                estimated_traffic
                * (website_conversion_rate / 100)
                * average_purchase_value
            )
        else:
            digital_revenue = 0.0

        additional_store_visits = (
            baseline_daily_store_traffic
            * campaign_duration_days
            * (estimated_traffic_uplift / 100)
        )

        uplifted_purchase_value = average_purchase_value * (
            1 + estimated_purchase_value_uplift / 100
        )

        offline_revenue = additional_store_visits * uplifted_purchase_value
        total_revenue = digital_revenue + offline_revenue

        roi = ((total_revenue - budget) / budget) * 100 if budget > 0 else 0.0

        score = 1
        if roi > 50:
            score += 4
        elif roi > 20:
            score += 3
        elif roi > 0:
            score += 2
        elif roi > -20:
            score += 1

        if not is_offline:
            if website_conversion_rate >= 5:
                score += 2
            elif website_conversion_rate >= 2:
                score += 1

        if estimated_traffic_uplift >= 20:
            score += 2
        elif estimated_traffic_uplift >= 10:
            score += 1

        if estimated_purchase_value_uplift >= 15:
            score += 1

        if budget > 0 and total_revenue / budget >= 3:
            score += 2
        elif budget > 0 and total_revenue / budget >= 1.5:
            score += 1

        score = min(score, 10)

        if roi > 30:
            recommendation = "RUN"
        elif roi >= 0:
            recommendation = "TEST"
        else:
            recommendation = "STOP"

        insights = []

        if not is_offline and estimated_traffic > 0 and website_conversion_rate >= 3:
            insights.append(
                "Digital campaign setup shows healthy online conversion potential."
            )

        if is_offline and estimated_offline_reach > 0:
            insights.append(
                "Offline campaign includes estimated reach based on media exposure assumptions."
            )

        if estimated_traffic_uplift >= 15:
            insights.append(
                "Campaign is expected to generate a meaningful uplift in store traffic."
            )

        if estimated_purchase_value_uplift > 0:
            insights.append(
                "Campaign may also improve average purchase value per customer."
            )

        if is_offline:
            insights.append(
                "Offline campaigns are evaluated using reach and store uplift assumptions instead of direct website conversion tracking."
            )

        if roi > 30:
            insights.append("Strong overall ROI potential.")
        elif roi < 0:
            insights.append("Estimated return may not justify the current budget.")

        if additional_store_visits < 100:
            insights.append(
                "Offline impact is relatively limited based on current uplift assumptions."
            )

        if budget > total_revenue:
            insights.append("Budget currently exceeds estimated total revenue.")

        if not insights:
            insights.append("Balanced campaign profile with moderate potential.")

        return {
            "digital_revenue": digital_revenue,
            "offline_revenue": offline_revenue,
            "total_revenue": total_revenue,
            "roi": roi,
            "score": score,
            "recommendation": recommendation,
            "additional_store_visits": additional_store_visits,
            "uplifted_purchase_value": uplifted_purchase_value,
            "insights": insights,
        }

    def app_header(title, subtitle=""):
        c = colors()
        return ft.Column(
            controls=[
                ft.Text(title, size=30, weight=ft.FontWeight.BOLD, color=c["text"]),
                ft.Text(subtitle, size=14, color=c["text_2"]),
            ],
            spacing=4,
        )

    def section_card(title, subtitle=""):
        c = colors()
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        title, size=18, weight=ft.FontWeight.BOLD, color=c["text"]
                    ),
                    ft.Text(subtitle, size=13, color=c["text_2"]),
                ],
                spacing=4,
            ),
            bgcolor=c["surface_3"],
            border=ft.border.all(1, c["border"]),
            border_radius=18,
            padding=16,
            shadow=soft_card_shadow(),
        )

    def clickable_section_card(title, subtitle, on_click):
        c = colors()
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        title, size=18, weight=ft.FontWeight.BOLD, color=c["text"]
                    ),
                    ft.Text(subtitle, size=13, color=c["text_2"]),
                ],
                spacing=4,
            ),
            bgcolor=c["surface_3"],
            border=ft.border.all(1, c["border"]),
            border_radius=18,
            padding=16,
            shadow=soft_card_shadow(),
            ink=True,
            on_click=on_click,
        )

    def glowing_icon(icon_text):
        c = colors()
        return ft.Container(
            width=46,
            height=46,
            border_radius=14,
            bgcolor="#312e81" if not c["is_light"] else "#c7d2fe",
            border=ft.border.all(1, "#6366f1"),
            shadow=ft.BoxShadow(
                blur_radius=18,
                color="#2563eb",
                offset=ft.Offset(0, 4),
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[ft.Text(icon_text, size=20)],
            ),
        )

    def action_card(title, subtitle, on_click, icon):
        c = colors()
        return ft.Container(
            content=ft.Row(
                controls=[
                    glowing_icon(icon),
                    ft.Container(width=12),
                    ft.Column(
                        controls=[
                            ft.Text(
                                title,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=c["text"],
                            ),
                            ft.Text(subtitle, size=13, color=c["text_2"]),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=c["surface_3"],
            border=ft.border.all(1, c["border"]),
            border_radius=22,
            padding=20,
            shadow=glow_shadow(22, "#1d4ed855"),
            ink=True,
            on_click=on_click,
        )

    def kpi_card(label, value, subtitle=""):
        c = colors()
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(label, size=12, color=c["text_3"]),
                    ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=c["text"]),
                    ft.Text(subtitle, size=11, color=c["text_2"]),
                ],
                spacing=4,
            ),
            bgcolor=c["surface_3"],
            border=ft.border.all(1, c["border"]),
            border_radius=18,
            padding=16,
            expand=True,
            shadow=soft_card_shadow(),
        )

    def recommendation_color(rec):
        c = colors()
        if rec == "RUN":
            return c["success"]
        if rec == "TEST":
            return c["warning"]
        return c["danger"]

    def recommendation_box(rec):
        return ft.Container(
            content=ft.Text(
                f"Recommendation: {rec}",
                color="white",
                weight=ft.FontWeight.BOLD,
                size=15,
            ),
            bgcolor=recommendation_color(rec),
            border_radius=16,
            padding=14,
            shadow=ft.BoxShadow(
                blur_radius=18,
                color=recommendation_color(rec),
                offset=ft.Offset(0, 6),
            ),
        )

    def input_field(label, value, on_change_handler):
        c = colors()
        return ft.TextField(
            label=label,
            value=value,
            border_radius=16,
            filled=True,
            bgcolor=c["field_bg"],
            border_color=c["border"],
            color=c["text"],
            label_style=ft.TextStyle(color=c["text_2"]),
            on_change=on_change_handler,
        )

    def primary_button(text, on_click, width=None, selected=False):
        c = colors()
        return ft.ElevatedButton(
            text,
            on_click=on_click,
            width=width,
            style=ft.ButtonStyle(
                bgcolor=c["selected_btn"] if selected else c["primary"],
                color="white",
                elevation=8,
                shape=ft.RoundedRectangleBorder(radius=16),
                text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
            ),
        )

    def secondary_glow_button(text, on_click, selected=False):
        c = colors()
        return ft.ElevatedButton(
            text,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=c["selected_btn"] if selected else c["unselected_btn"],
                color="white" if not c["is_light"] else "#0f172a",
                elevation=10 if selected else 3,
                shape=ft.RoundedRectangleBorder(radius=16),
                text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                shadow_color="#2563eb" if selected else "transparent",
            ),
        )

    def outline_glow_button(text, on_click):
        c = colors()
        return ft.OutlinedButton(
            text,
            on_click=on_click,
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, "#60a5fa"),
                color=c["text_2"],
                shape=ft.RoundedRectangleBorder(radius=16),
                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            ),
        )

    def icon_glow_button(icon, on_click):
        c = colors()
        return ft.Container(
            width=56,
            height=56,
            bgcolor=c["icon_btn_bg"],
            border=ft.border.all(1, "#60a5fa"),
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=18,
                color="#2563eb66",
                offset=ft.Offset(0, 4),
            ),
            ink=True,
            on_click=on_click,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        icon,
                        color="white" if not c["is_light"] else "#0f172a",
                        size=22,
                    )
                ],
            ),
        )

    def save_field(key):
        def handler(e):
            form_state[key] = e.control.value
        return handler

    def show_snackbar(message: str):
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        page.update()

    def reset_campaign_form():
        form_state.update(
            {
                "campaign_name": "",
                "campaign_mode": "Digital",
                "channel": "Social Media",
                "campaign_type": "Branding",
                "budget": "1000",
                "estimated_traffic": "10000",
                "estimated_offline_reach": "50000",
                "website_conversion_rate": "2.5",
                "campaign_duration_days": "7",
                "average_purchase_value": "50",
                "estimated_purchase_value_uplift": "0",
                "baseline_daily_store_traffic": "1000",
                "estimated_traffic_uplift": "10",
            }
        )
        latest_campaign["data"] = None
        editing_campaign_id["value"] = None

    def load_campaign_into_form(campaign):
        form_state["campaign_name"] = campaign.get("Campaign Name", "")
        form_state["channel"] = campaign.get("Channel", "Social Media")
        form_state["campaign_mode"] = (
            "Offline" if campaign.get("Channel") == "Offline" else "Digital"
        )
        form_state["campaign_type"] = campaign.get("Campaign Type", "Branding")
        form_state["budget"] = str(campaign.get("Budget (€)", "1000"))
        form_state["estimated_traffic"] = str(
            campaign.get("Estimated Digital Traffic", "10000")
        )
        form_state["estimated_offline_reach"] = str(
            campaign.get("Estimated Offline Reach", "50000")
        )
        form_state["website_conversion_rate"] = str(
            campaign.get("Website Conversion Rate (%)", "2.5")
        )
        form_state["campaign_duration_days"] = str(
            campaign.get("Campaign Duration (days)", "7")
        )
        form_state["average_purchase_value"] = str(
            campaign.get("Average Purchase Value (€)", "50")
        )
        form_state["estimated_purchase_value_uplift"] = str(
            campaign.get("Purchase Value Uplift (%)", "0")
        )
        form_state["baseline_daily_store_traffic"] = str(
            campaign.get("Baseline Daily Store Traffic", "1000")
        )
        form_state["estimated_traffic_uplift"] = str(
            campaign.get("Traffic Uplift (%)", "10")
        )
        latest_campaign["data"] = campaign.copy()

    # -----------------------------
    # Navigation
    # -----------------------------
    def start_app(e):
        current_view["screen"] = "home"
        render()

    def go_start(e):
        current_view["screen"] = "start"
        render()

    def go_home(e):
        current_view["screen"] = "home"
        render()

    def go_new_campaign(e):
        reset_campaign_form()
        current_view["screen"] = "new_campaign"
        render()

    def go_library(e):
        current_view["screen"] = "library"
        render()

    def go_simulator(e):
        current_view["screen"] = "simulator"
        render()

    def go_notes(e):
        current_view["screen"] = "notes"
        render()

    def go_notes_editor(e):
        note_form_state["title"] = ""
        note_form_state["content"] = ""
        editing_note_id["value"] = None
        current_view["screen"] = "notes_editor"
        render()

    def go_settings(e):
        current_view["screen"] = "settings"
        render()

    def open_notes(e):
        current_view["screen"] = "notes"
        render()

    def open_settings(e):
        current_view["screen"] = "settings"
        render()

    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = "#eef2ff"
        else:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = "#0b1020"
        render()

    # -----------------------------
    # Campaign actions
    # -----------------------------
    def edit_campaign(campaign_id):
        for campaign in campaigns:
            if campaign.get("id") == campaign_id:
                editing_campaign_id["value"] = campaign_id
                load_campaign_into_form(campaign)
                current_view["screen"] = "new_campaign"
                render()
                return

    def delete_campaign(campaign_id):
        nonlocal campaigns
        campaigns = [c for c in campaigns if c.get("id") != campaign_id]
        save_app_data()
        show_snackbar("Campaign deleted.")
        render()

    # -----------------------------
    # Note actions
    # -----------------------------
    def edit_note(note_id):
        for note in notes:
            if note.get("id") == note_id:
                editing_note_id["value"] = note_id
                note_form_state["title"] = note.get("title", "")
                note_form_state["content"] = note.get("content", "")
                current_view["screen"] = "notes_editor"
                render()
                return

    def delete_note(note_id):
        nonlocal notes
        notes = [n for n in notes if n.get("id") != note_id]
        save_app_data()
        show_snackbar("Note deleted.")
        render()

    # -----------------------------
    # Render
    # -----------------------------
    def render():
        page.controls.clear()
        screen = current_view["screen"]
        c = colors()
        is_light = c["is_light"]

        if screen == "start":
            page.add(
                ft.Container(
                    expand=True,
                    bgcolor=c["page_bg"],
                    padding=ft.padding.only(top=80, bottom=30),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=380,
                                padding=32,
                                bgcolor=c["surface"],
                                border_radius=settings_state["card_radius"],
                                border=ft.border.all(1, c["border"]),
                                shadow=ft.BoxShadow(
                                    blur_radius=settings_state["glow_intensity"],
                                    color="#2563eb",
                                    offset=ft.Offset(0, 8),
                                ),
                                content=ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=20,
                                    controls=[
                                        ft.Container(
                                            width=70,
                                            height=70,
                                            border_radius=20,
                                            bgcolor="#4f46e5",
                                            shadow=ft.BoxShadow(
                                                blur_radius=20,
                                                color="#2563eb",
                                                offset=ft.Offset(0, 4),
                                            ),
                                            content=ft.Row(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                controls=[
                                                    ft.Text(
                                                        "✦",
                                                        size=28,
                                                        weight=ft.FontWeight.BOLD,
                                                        color="white",
                                                    )
                                                ],
                                            ),
                                        ),
                                        ft.Text(
                                            "Campaign OS",
                                            size=36,
                                            weight=ft.FontWeight.BOLD,
                                            color=c["text"],
                                        ),
                                        ft.Text(
                                            "Marketing Decision Engine",
                                            size=15,
                                            color=c["text_2"],
                                        ),
                                        ft.Text(
                                            "Evaluate campaigns across digital and offline channels with a premium decision system.",
                                            size=13,
                                            color=c["text_3"],
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        ft.Container(height=10),
                                        primary_button("Start", start_app, width=200),
                                    ],
                                ),
                            ),
                            ft.Container(height=18),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=18,
                                controls=[
                                    icon_glow_button(
                                        ft.Icons.STICKY_NOTE_2_OUTLINED, open_notes
                                    ),
                                    icon_glow_button(
                                        ft.Icons.SETTINGS_OUTLINED, open_settings
                                    ),
                                    icon_glow_button(
                                        ft.Icons.LIGHT_MODE_OUTLINED
                                        if not is_light
                                        else ft.Icons.DARK_MODE_OUTLINED,
                                        toggle_theme,
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )

        elif screen == "notes":
            controls = [
                app_header("Saved Notes", "Add, edit and delete campaign notes."),
                ft.Container(height=16),
                primary_button("Add New Note", go_notes_editor),
                ft.Container(height=18),
            ]

            if not notes:
                controls.append(
                    ft.Container(
                        content=ft.Text(
                            "No saved notes yet.",
                            color=c["text_2"],
                            size=16,
                        ),
                        bgcolor=c["surface_3"],
                        border=ft.border.all(1, c["border"]),
                        border_radius=20,
                        padding=20,
                        shadow=soft_card_shadow(),
                    )
                )
            else:
                for note in notes:
                    controls.append(
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        note.get("title", "Untitled Note"),
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=c["text"],
                                    ),
                                    ft.Text(
                                        (note.get("content", "")[:140] + "...")
                                        if len(note.get("content", "")) > 140
                                        else note.get("content", ""),
                                        color=c["text_2"],
                                        size=13,
                                        selectable=True,
                                    ),
                                    ft.Container(height=8),
                                    ft.Row(
                                        controls=[
                                            primary_button(
                                                "Edit",
                                                lambda e, nid=note["id"]: edit_note(nid),
                                            ),
                                            ft.ElevatedButton(
                                                "Delete",
                                                on_click=lambda e, nid=note["id"]: delete_note(
                                                    nid
                                                ),
                                                style=ft.ButtonStyle(
                                                    bgcolor=c["danger"],
                                                    color="white",
                                                    shape=ft.RoundedRectangleBorder(
                                                        radius=16
                                                    ),
                                                ),
                                            ),
                                        ],
                                        wrap=True,
                                    ),
                                ],
                                spacing=8,
                            ),
                            bgcolor=c["surface_3"],
                            border=ft.border.all(1, c["border"]),
                            border_radius=18,
                            padding=16,
                            margin=ft.margin.only(bottom=12),
                            shadow=soft_card_shadow(),
                        )
                    )

            controls.extend(
                [
                    ft.Container(height=20),
                    secondary_glow_button("Back to Dashboard", go_home),
                ]
            )

            page.add(
                ft.Container(
                    expand=True,
                    bgcolor=c["page_bg"],
                    padding=24,
                    content=ft.Column(
                        controls=controls,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                )
            )

        elif screen == "notes_editor":

            def save_note(e):
                title = (note_form_state["title"] or "").strip()
                content = (note_form_state["content"] or "").strip()

                if not title:
                    title = "Untitled Note"

                if not content:
                    show_snackbar("Note content cannot be empty.")
                    return

                if editing_note_id["value"] is not None:
                    for note in notes:
                        if note.get("id") == editing_note_id["value"]:
                            note["title"] = title
                            note["content"] = content
                            break
                    show_snackbar("Note updated.")
                else:
                    notes.append(
                        {
                            "id": str(uuid.uuid4()),
                            "title": title,
                            "content": content,
                        }
                    )
                    show_snackbar("Note saved.")

                save_app_data()
                current_view["screen"] = "notes"
                render()

            title_field = ft.TextField(
                value=note_form_state["title"],
                label="Note Title",
                border_radius=16,
                filled=True,
                bgcolor=c["field_bg"],
                border_color=c["border"],
                color=c["text"],
                label_style=ft.TextStyle(color=c["text_2"]),
                on_change=lambda e: note_form_state.update({"title": e.control.value}),
            )

            notes_field = ft.TextField(
                value=note_form_state["content"],
                multiline=True,
                min_lines=18,
                max_lines=24,
                expand=True,
                border_radius=18,
                filled=True,
                bgcolor=c["field_bg"],
                border_color=c["border"],
                color=c["text"],
                label="Note Content",
                label_style=ft.TextStyle(color=c["text_2"]),
                on_change=lambda e: note_form_state.update({"content": e.control.value}),
            )

            page.add(
                ft.Container(
                    expand=True,
                    bgcolor=c["page_bg"],
                    padding=24,
                    content=ft.Column(
                        expand=True,
                        controls=[
                            app_header(
                                "Edit Note" if editing_note_id["value"] else "New Note",
                                "Create or update your campaign note.",
                            ),
                            ft.Text(
                                f"Saved locally in: {DATA_FILE.name}",
                                size=12,
                                color=c["text_3"],
                            ),
                            ft.Container(height=16),
                            title_field,
                            ft.Container(height=16),
                            ft.Container(
                                content=ft.Container(
                                    content=notes_field,
                                    padding=20,
                                    border_radius=22,
                                    bgcolor=c["field_bg"],
                                ),
                                expand=True,
                                padding=4,
                                border_radius=26,
                                shadow=ft.BoxShadow(
                                    blur_radius=40,
                                    color="#2563eb",
                                    offset=ft.Offset(0, 10),
                                ),
                            ),
                            ft.Container(height=16),
                            ft.Row(
                                controls=[
                                    primary_button("Save Note", save_note),
                                    outline_glow_button("Back to Notes", go_notes),
                                ],
                                wrap=True,
                            ),
                        ],
                    ),
                )
            )

        elif screen == "settings":
            glow_value = ft.Text(
                f"{settings_state['glow_intensity']}",
                color=c["text"],
                size=14,
            )
            radius_value = ft.Text(
                f"{settings_state['card_radius']}",
                color=c["text"],
                size=14,
            )

            glow_preview_ref = ft.Ref[ft.Container]()
            radius_preview_ref = ft.Ref[ft.Container]()

            def on_glow_change(e):
                new_glow = int(e.control.value)
                settings_state["glow_intensity"] = new_glow
                glow_value.value = str(new_glow)

                if glow_preview_ref.current:
                    glow_preview_ref.current.shadow = ft.BoxShadow(
                        blur_radius=new_glow,
                        color="#2563eb",
                        offset=ft.Offset(0, 6),
                    )

                page.update()

            def on_radius_change(e):
                new_radius = int(e.control.value)
                settings_state["card_radius"] = new_radius
                radius_value.value = str(new_radius)

                if radius_preview_ref.current:
                    radius_preview_ref.current.border_radius = new_radius

                page.update()

            def save_settings(e):
                save_app_data()
                show_snackbar("Settings saved.")
                render()

            glow_slider = ft.Slider(
                min=10,
                max=60,
                divisions=10,
                value=settings_state["glow_intensity"],
                active_color="#4f46e5",
                inactive_color="#334155",
                on_change=on_glow_change,
            )

            radius_slider = ft.Slider(
                min=18,
                max=40,
                divisions=11,
                value=settings_state["card_radius"],
                active_color="#4f46e5",
                inactive_color="#334155",
                on_change=on_radius_change,
            )

            glow_preview_card = ft.Container(
                ref=glow_preview_ref,
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Glow Intensity",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=c["text"],
                        ),
                        ft.Text(
                            "Adjust the strength of the blue glow.",
                            size=13,
                            color=c["text_2"],
                        ),
                    ],
                    spacing=4,
                ),
                bgcolor=c["surface_3"],
                border=ft.border.all(1, c["border"]),
                border_radius=18,
                padding=16,
                shadow=ft.BoxShadow(
                    blur_radius=settings_state["glow_intensity"],
                    color="#2563eb",
                    offset=ft.Offset(0, 6),
                ),
            )

            radius_preview_card = ft.Container(
                ref=radius_preview_ref,
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Card Radius",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=c["text"],
                        ),
                        ft.Text(
                            "Adjust roundness of the main start card.",
                            size=13,
                            color=c["text_2"],
                        ),
                    ],
                    spacing=4,
                ),
                bgcolor=c["surface_3"],
                border=ft.border.all(1, c["border"]),
                border_radius=settings_state["card_radius"],
                padding=16,
                shadow=ft.BoxShadow(
                    blur_radius=18,
                    color="#2563eb",
                    offset=ft.Offset(0, 6),
                ),
            )

            page.add(
                ft.Container(
                    expand=True,
                    bgcolor=c["page_bg"],
                    padding=24,
                    content=ft.Column(
                        controls=[
                            app_header(
                                "Settings",
                                "Customize the visual style of Campaign OS.",
                            ),
                            ft.Container(height=16),
                            glow_preview_card,
                            ft.Container(height=10),
                            glow_slider,
                            glow_value,
                            ft.Container(height=20),
                            radius_preview_card,
                            ft.Container(height=10),
                            radius_slider,
                            radius_value,
                            ft.Container(height=20),
                            ft.Row(
                                controls=[
                                    primary_button("Save Settings", save_settings),
                                    outline_glow_button("Back to Start", go_start),
                                ],
                                wrap=True,
                            ),
                        ],
                    ),
                )
            )

        elif screen == "home":
            notes_preview = (
                f"{len(notes)} saved notes"
                if notes
                else "No saved notes yet."
            )

            page.add(
                ft.Container(
                    expand=True,
                    bgcolor=c["page_bg"],
                    padding=24,
                    content=ft.Column(
                        controls=[
                            app_header("Dashboard", "Choose what you want to do next."),
                            ft.Container(height=20),
                            action_card(
                                "New Campaign",
                                "Create and evaluate a new campaign scenario.",
                                go_new_campaign,
                                "✚",
                            ),
                            ft.Container(height=14),
                            action_card(
                                "Campaign Library",
                                "View, edit and delete saved campaigns.",
                                go_library,
                                "📁",
                            ),
                            ft.Container(height=14),
                            action_card(
                                "Quick Simulator",
                                "Test assumptions and see ROI potential fast.",
                                go_simulator,
                                "⚡",
                            ),
                            ft.Container(height=18),
                            clickable_section_card(
                                "Saved Notes", notes_preview, go_notes
                            ),
                            ft.Container(expand=True),
                            secondary_glow_button("Back to Start", go_start),
                        ],
                    ),
                )
            )

        elif screen == "new_campaign":
            is_offline = form_state["campaign_mode"] == "Offline"

            campaign_name_field = input_field(
                "Campaign Name",
                form_state["campaign_name"],
                save_field("campaign_name"),
            )

            digital_channel_dropdown = ft.Dropdown(
                label="Digital Channel",
                value=form_state["channel"]
                if form_state["channel"] != "Offline"
                else "Social Media",
                border_radius=14,
                filled=True,
                bgcolor=c["field_bg"],
                border_color=c["border"],
                color=c["text"],
                options=[
                    ft.dropdown.Option("Social Media"),
                    ft.dropdown.Option("Google Ads"),
                    ft.dropdown.Option("Email"),
                    ft.dropdown.Option("Influencer"),
                    ft.dropdown.Option("Display Ads"),
                ],
            )

            campaign_type_dropdown = ft.Dropdown(
                label="Campaign Type",
                value=form_state["campaign_type"],
                border_radius=14,
                filled=True,
                bgcolor=c["field_bg"],
                border_color=c["border"],
                color=c["text"],
                options=[
                    ft.dropdown.Option("Branding"),
                    ft.dropdown.Option("Performance"),
                    ft.dropdown.Option("Promotion"),
                ],
            )

            budget_field = input_field(
                "Budget (€)", form_state["budget"], save_field("budget")
            )
            duration_field = input_field(
                "Campaign Duration (days)",
                form_state["campaign_duration_days"],
                save_field("campaign_duration_days"),
            )
            avg_purchase_field = input_field(
                "Average Purchase Value (€)",
                form_state["average_purchase_value"],
                save_field("average_purchase_value"),
            )
            purchase_uplift_field = input_field(
                "Estimated Purchase Value Uplift (%)",
                form_state["estimated_purchase_value_uplift"],
                save_field("estimated_purchase_value_uplift"),
            )
            baseline_store_field = input_field(
                "Baseline Daily Store Traffic",
                form_state["baseline_daily_store_traffic"],
                save_field("baseline_daily_store_traffic"),
            )
            traffic_uplift_field = input_field(
                "Estimated Traffic Uplift (%)",
                form_state["estimated_traffic_uplift"],
                save_field("estimated_traffic_uplift"),
            )
            digital_traffic_field = input_field(
                "Estimated Digital Traffic",
                form_state["estimated_traffic"],
                save_field("estimated_traffic"),
            )
            conversion_field = input_field(
                "Website Conversion Rate (%)",
                form_state["website_conversion_rate"],
                save_field("website_conversion_rate"),
            )
            offline_reach_field = input_field(
                "Estimated Offline Reach",
                form_state["estimated_offline_reach"],
                save_field("estimated_offline_reach"),
            )

            def set_mode_digital(e):
                form_state["campaign_mode"] = "Digital"
                if form_state["channel"] == "Offline":
                    form_state["channel"] = "Social Media"
                render()

            def set_mode_offline(e):
                form_state["campaign_mode"] = "Offline"
                form_state["channel"] = "Offline"
                render()

            def calculate(e):
                form_state["campaign_name"] = campaign_name_field.value or ""
                form_state["campaign_type"] = campaign_type_dropdown.value or "Branding"
                form_state["budget"] = budget_field.value or "0"
                form_state["campaign_duration_days"] = duration_field.value or "0"
                form_state["average_purchase_value"] = avg_purchase_field.value or "0"
                form_state["estimated_purchase_value_uplift"] = (
                    purchase_uplift_field.value or "0"
                )
                form_state["baseline_daily_store_traffic"] = (
                    baseline_store_field.value or "0"
                )
                form_state["estimated_traffic_uplift"] = (
                    traffic_uplift_field.value or "0"
                )
                form_state["estimated_traffic"] = digital_traffic_field.value or "0"
                form_state["website_conversion_rate"] = conversion_field.value or "0"
                form_state["estimated_offline_reach"] = offline_reach_field.value or "0"

                form_state["channel"] = (
                    "Offline"
                    if form_state["campaign_mode"] == "Offline"
                    else (digital_channel_dropdown.value or "Social Media")
                )

                campaign_name = form_state["campaign_name"] or "Untitled Campaign"
                channel = form_state["channel"]
                campaign_type = form_state["campaign_type"]
                budget = to_float(form_state["budget"], 1000.0)
                estimated_traffic = to_int(form_state["estimated_traffic"], 10000)
                estimated_offline_reach = to_int(
                    form_state["estimated_offline_reach"], 50000
                )
                website_conversion_rate = to_float(
                    form_state["website_conversion_rate"], 2.5
                )
                campaign_duration_days = to_int(
                    form_state["campaign_duration_days"], 7
                )
                average_purchase_value = to_float(
                    form_state["average_purchase_value"], 50.0
                )
                estimated_purchase_value_uplift = to_float(
                    form_state["estimated_purchase_value_uplift"], 0.0
                )
                baseline_daily_store_traffic = to_int(
                    form_state["baseline_daily_store_traffic"], 1000
                )
                estimated_traffic_uplift = to_float(
                    form_state["estimated_traffic_uplift"], 10.0
                )

                metrics = calculate_campaign_metrics(
                    channel=channel,
                    budget=budget,
                    estimated_traffic=estimated_traffic,
                    website_conversion_rate=website_conversion_rate,
                    estimated_offline_reach=estimated_offline_reach,
                    campaign_duration_days=campaign_duration_days,
                    average_purchase_value=average_purchase_value,
                    estimated_purchase_value_uplift=estimated_purchase_value_uplift,
                    baseline_daily_store_traffic=baseline_daily_store_traffic,
                    estimated_traffic_uplift=estimated_traffic_uplift,
                )

                campaign_id = (
                    editing_campaign_id["value"]
                    if editing_campaign_id["value"] is not None
                    else str(uuid.uuid4())
                )

                latest_campaign["data"] = {
                    "id": campaign_id,
                    "Campaign Name": campaign_name,
                    "Channel": channel,
                    "Campaign Type": campaign_type,
                    "Budget (€)": budget,
                    "Estimated Digital Traffic": estimated_traffic,
                    "Estimated Offline Reach": estimated_offline_reach,
                    "Website Conversion Rate (%)": website_conversion_rate,
                    "Campaign Duration (days)": campaign_duration_days,
                    "Average Purchase Value (€)": average_purchase_value,
                    "Purchase Value Uplift (%)": estimated_purchase_value_uplift,
                    "Baseline Daily Store Traffic": baseline_daily_store_traffic,
                    "Traffic Uplift (%)": estimated_traffic_uplift,
                    "Total Revenue (€)": metrics["total_revenue"],
                    "Digital Revenue (€)": metrics["digital_revenue"],
                    "Offline Revenue (€)": metrics["offline_revenue"],
                    "ROI (%)": metrics["roi"],
                    "Efficiency Score": metrics["score"],
                    "Recommendation": metrics["recommendation"],
                    "Additional Store Visits": metrics["additional_store_visits"],
                    "Insights": metrics["insights"],
                }

                render()

            def save_campaign(e):
                if latest_campaign["data"] is None:
                    show_snackbar("First calculate the campaign.")
                    return

                if editing_campaign_id["value"] is not None:
                    for idx, campaign in enumerate(campaigns):
                        if campaign.get("id") == editing_campaign_id["value"]:
                            campaigns[idx] = latest_campaign["data"].copy()
                            save_app_data()
                            show_snackbar("Campaign updated.")
                            editing_campaign_id["value"] = None
                            render()
                            return

                campaigns.append(latest_campaign["data"].copy())
                save_app_data()
                show_snackbar("Campaign saved.")
                editing_campaign_id["value"] = None
                render()

            controls = [
                app_header(
                    "Edit Campaign" if editing_campaign_id["value"] else "New Campaign",
                    "Build and evaluate your campaign scenario.",
                ),
                ft.Container(height=16),
                section_card(
                    "Campaign Mode", "Choose how the campaign should be measured."
                ),
                ft.Container(height=12),
                ft.Row(
                    controls=[
                        secondary_glow_button(
                            "Digital Campaign",
                            set_mode_digital,
                            selected=not is_offline,
                        ),
                        secondary_glow_button(
                            "Offline Campaign",
                            set_mode_offline,
                            selected=is_offline,
                        ),
                    ],
                    wrap=True,
                ),
                ft.Text(
                    "Offline mode active." if is_offline else "Digital mode active.",
                    color=c["text_2"],
                    size=12,
                ),
                ft.Container(height=22),
                section_card("Campaign Basics", "Core campaign information."),
                ft.Container(height=16),
                campaign_name_field,
                ft.Container(height=14),
            ]

            if not is_offline:
                controls.extend(
                    [
                        digital_channel_dropdown,
                        ft.Container(height=14),
                        campaign_type_dropdown,
                        ft.Container(height=14),
                        budget_field,
                        ft.Container(height=14),
                        duration_field,
                        ft.Container(height=22),
                        section_card(
                            "Digital Performance",
                            "Traffic and website conversion assumptions.",
                        ),
                        ft.Container(height=16),
                        digital_traffic_field,
                        ft.Container(height=14),
                        conversion_field,
                        ft.Container(height=22),
                        section_card(
                            "Financial Assumptions",
                            "Purchase value and basket uplift.",
                        ),
                        ft.Container(height=16),
                        avg_purchase_field,
                        ft.Container(height=14),
                        purchase_uplift_field,
                        ft.Container(height=22),
                        section_card("Offline Impact", "Store uplift assumptions."),
                        ft.Container(height=16),
                        baseline_store_field,
                        ft.Container(height=14),
                        traffic_uplift_field,
                    ]
                )
            else:
                controls.extend(
                    [
                        campaign_type_dropdown,
                        ft.Container(height=14),
                        budget_field,
                        ft.Container(height=14),
                        duration_field,
                        ft.Container(height=22),
                        section_card(
                            "Offline Reach",
                            "Estimated number of people exposed to the offline campaign.",
                        ),
                        ft.Container(height=16),
                        offline_reach_field,
                        ft.Container(height=22),
                        section_card(
                            "Financial Assumptions",
                            "Purchase value and basket uplift.",
                        ),
                        ft.Container(height=16),
                        avg_purchase_field,
                        ft.Container(height=14),
                        purchase_uplift_field,
                        ft.Container(height=22),
                        section_card("Offline Impact", "Store uplift assumptions."),
                        ft.Container(height=16),
                        baseline_store_field,
                        ft.Container(height=14),
                        traffic_uplift_field,
                    ]
                )

            controls.extend(
                [
                    ft.Container(height=24),
                    ft.Row(
                        controls=[
                            primary_button(
                                "Calculate Campaign Potential", calculate
                            ),
                            outline_glow_button("Back to Dashboard", go_home),
                        ],
                        wrap=True,
                    ),
                ]
            )

            if latest_campaign["data"] is not None:
                data = latest_campaign["data"]
                controls.extend(
                    [
                        ft.Container(height=24),
                        section_card("Results", "Campaign performance output."),
                        ft.Container(height=16),
                        ft.Row(
                            controls=[
                                kpi_card(
                                    "Total Revenue",
                                    f"€{data['Total Revenue (€)']:,.0f}",
                                    "Projected return",
                                ),
                                kpi_card(
                                    "ROI",
                                    f"{data['ROI (%)']:.2f}%",
                                    "Return vs budget",
                                ),
                            ],
                        ),
                        ft.Container(height=12),
                        ft.Row(
                            controls=[
                                kpi_card(
                                    "Score",
                                    f"{data['Efficiency Score']}/10",
                                    "Efficiency score",
                                ),
                                kpi_card(
                                    "Recommendation",
                                    data["Recommendation"],
                                    "Decision output",
                                ),
                            ],
                        ),
                        ft.Container(height=12),
                        ft.Row(
                            controls=[
                                kpi_card(
                                    "Digital Revenue",
                                    "N/A"
                                    if data["Channel"] == "Offline"
                                    else f"€{data['Digital Revenue (€)']:,.0f}",
                                    "Online contribution",
                                ),
                                kpi_card(
                                    "Offline Revenue",
                                    f"€{data['Offline Revenue (€)']:,.0f}",
                                    "Store contribution",
                                ),
                            ],
                        ),
                        ft.Container(height=12),
                        kpi_card(
                            "Additional Store Visits",
                            f"{data['Additional Store Visits']:,.0f}",
                            "Incremental store traffic",
                        ),
                        ft.Container(height=12),
                        recommendation_box(data["Recommendation"]),
                        ft.Container(height=16),
                        section_card("Insights", "Key takeaways from your scenario."),
                    ]
                )

                for insight in data["Insights"]:
                    controls.append(
                        ft.Container(
                            content=ft.Text(f"• {insight}", color=c["text"], size=13),
                            bgcolor=c["surface_3"],
                            border=ft.border.all(1, c["border"]),
                            border_radius=14,
                            padding=14,
                            margin=ft.margin.only(top=10),
                            shadow=soft_card_shadow(),
                        )
                    )

                controls.extend(
                    [
                        ft.Container(height=16),
                        ft.ElevatedButton(
                            "Update Campaign"
                            if editing_campaign_id["value"]
                            else "Save Campaign to Library",
                            on_click=save_campaign,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=16),
                                bgcolor="#16a34a",
                                color="white",
                                elevation=8,
                                text_style=ft.TextStyle(
                                    weight=ft.FontWeight.BOLD
                                ),
                            ),
                        ),
                    ]
                )

            page.add(
                ft.Container(
                    expand=True,
                    bgcolor=c["page_bg"],
                    padding=24,
                    content=ft.Column(
                        controls=controls,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                )
            )

        elif screen == "library":
            controls = [
                app_header("Campaign Library", "Saved campaign scenarios."),
                ft.Container(height=16),
            ]

            if not campaigns:
                controls.append(
                    ft.Container(
                        content=ft.Text(
                            "No campaigns saved yet.", color=c["text_2"], size=16
                        ),
                        bgcolor=c["surface_3"],
                        border=ft.border.all(1, c["border"]),
                        border_radius=20,
                        padding=20,
                        shadow=soft_card_shadow(),
                    )
                )
            else:
                for campaign in campaigns:
                    controls.append(
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        campaign["Campaign Name"],
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=c["text"],
                                    ),
                                    ft.Text(
                                        f"{campaign['Channel']} • ROI {campaign['ROI (%)']:.2f}% • {campaign['Recommendation']}",
                                        color=c["text_2"],
                                        size=13,
                                    ),
                                    ft.Container(height=8),
                                    ft.Row(
                                        controls=[
                                            primary_button(
                                                "Edit",
                                                lambda e, cid=campaign["id"]: edit_campaign(
                                                    cid
                                                ),
                                            ),
                                            ft.ElevatedButton(
                                                "Delete",
                                                on_click=lambda e, cid=campaign["id"]: delete_campaign(
                                                    cid
                                                ),
                                                style=ft.ButtonStyle(
                                                    bgcolor=c["danger"],
                                                    color="white",
                                                    shape=ft.RoundedRectangleBorder(
                                                        radius=16
                                                    ),
                                                ),
                                            ),
                                        ],
                                        wrap=True,
                                    ),
                                ],
                                spacing=4,
                            ),
                            bgcolor=c["surface_3"],
                            border=ft.border.all(1, c["border"]),
                            border_radius=18,
                            padding=16,
                            margin=ft.margin.only(bottom=12),
                            shadow=soft_card_shadow(),
                        )
                    )

            controls.extend(
                [
                    ft.Container(height=20),
                    secondary_glow_button("Back to Dashboard", go_home),
                ]
            )

            page.add(
                ft.Container(
                    expand=True,
                    bgcolor=c["page_bg"],
                    padding=24,
                    content=ft.Column(
                        controls=controls,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                )
            )

        elif screen == "simulator":
            budget_slider = ft.Slider(min=100, max=20000, value=2400, divisions=199)
            traffic_slider = ft.Slider(min=0, max=100000, value=10000, divisions=100)
            conversion_slider = ft.Slider(min=0, max=10, value=2.5, divisions=100)
            purchase_slider = ft.Slider(min=5, max=500, value=50, divisions=99)
            uplift_slider = ft.Slider(min=0, max=100, value=10, divisions=100)
            duration_slider = ft.Slider(min=1, max=60, value=7, divisions=59)

            result_text = ft.Text(color=c["text"], size=16)

            def simulate(e):
                metrics = calculate_campaign_metrics(
                    channel="Social Media",
                    budget=float(budget_slider.value),
                    estimated_traffic=int(traffic_slider.value),
                    website_conversion_rate=float(conversion_slider.value),
                    estimated_offline_reach=0,
                    campaign_duration_days=int(duration_slider.value),
                    average_purchase_value=float(purchase_slider.value),
                    estimated_purchase_value_uplift=0.0,
                    baseline_daily_store_traffic=1000,
                    estimated_traffic_uplift=float(uplift_slider.value),
                )
                result_text.value = (
                    f"ROI: {metrics['roi']:.2f}% | Recommendation: {metrics['recommendation']}"
                )
                page.update()

            page.add(
                ft.Container(
                    expand=True,
                    bgcolor=c["page_bg"],
                    padding=24,
                    content=ft.Column(
                        controls=[
                            app_header(
                                "Quick Simulator",
                                "Stress-test campaign assumptions.",
                            ),
                            ft.Container(height=16),
                            ft.Text("Budget", color=c["text"]),
                            budget_slider,
                            ft.Text("Estimated Digital Traffic", color=c["text"]),
                            traffic_slider,
                            ft.Text("Website Conversion Rate (%)", color=c["text"]),
                            conversion_slider,
                            ft.Text("Average Purchase Value (€)", color=c["text"]),
                            purchase_slider,
                            ft.Text("Traffic Uplift (%)", color=c["text"]),
                            uplift_slider,
                            ft.Text("Campaign Duration (days)", color=c["text"]),
                            duration_slider,
                            ft.Container(height=12),
                            primary_button("Run Simulation", simulate),
                            result_text,
                            ft.Container(height=12),
                            secondary_glow_button("Back to Dashboard", go_home),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                )
            )

        page.update()

    load_app_data()
    render()


ft.app(
    target=main,
    view=ft.AppView.WEB_BROWSER,
    host="0.0.0.0",
    port=int(os.getenv("PORT", 8550)),
    assets_dir="assets",
)
