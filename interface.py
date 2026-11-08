from nicegui import ui
from dataclasses import dataclass, field
import asyncio
from alerts import send_family_alert
from datetime import datetime


# define class for transcript with attributes text and speaker
@dataclass
class TranscriptChunk:
    text: str
    speaker: str = "Unknown"
    timestamp: datetime = field(default_factory=datetime.now)

# define class for Assessment with attributes risk, tactics, and message
@dataclass
class Assessment:
    risk: int
    tactics: list[str] = field(default_factory=list)
    message: str = "Guardian is listening."

# Shared application state, this is a dictionary that will be updated by the agent as teh conversation progresses.
state = {
    'transcript': [],
    'risk': 0,
    'tactics': [],
    'message': 'Guardian is listening.',
    'alerted': False,
    'alert_count': 0
}
on_reset = []  # List of functions to call when the call is reset
def reset_call():
    state['transcript'].clear()
    state['risk'] = 0
    state['tactics'] = []
    state['message'] = 'Guardian is listening.'
    state['alerted'] = False
    for fn in on_reset:
        fn()

# Receive transcript chunks
def add_transcript(chunk: TranscriptChunk):
    state['transcript'].append(chunk)


# Receive scam assessments
def add_assessment(a: Assessment):
    previous_risk = state['risk']

    state['risk'] = a.risk
    state['tactics'] = a.tactics
    state['message'] = a.message

    if a.risk >= 80 and previous_risk < 80 and not state['alerted']:
        if send_family_alert(a.risk, a.message):
            state['alert_count'] += 1
        state['alerted'] = True

async def simulate_call():
    # Prevent previous demonstration data from remaining
    state['transcript'].clear()
    state['risk'] = 0
    state['tactics'] = []
    state['message'] = 'Guardian is listening.'
    state['alerted'] = False

    # First caller message
    add_transcript(TranscriptChunk(
        text="Hello, I'm calling from your bank's security department.",
        speaker="Caller"
    ))

    await asyncio.sleep(3)

    # Second caller message
    add_transcript(TranscriptChunk(
        text="We've detected suspicious activity on your account.",
        speaker="Caller"
    ))

    add_assessment(Assessment(
        risk=45,
        tactics=["Possible impersonation"],
        message="Be cautious. The caller is claiming to represent your bank."
    ))

    await asyncio.sleep(4)

    # Third caller message
    add_transcript(TranscriptChunk(
        text="You must transfer your money immediately to protect it.",
        speaker="Caller"
    ))

    await asyncio.sleep(2)

    # Final high-risk assessment
    add_assessment(Assessment(
        risk=85,
        tactics=[
            "Impersonation",
            "Urgency",
            "Pressure to transfer money"
        ],
        message="High risk! Do not transfer money or share your banking details. Contact your bank using its official number."
    ))

#Render the web page

@ui.page('/')
def home():

    ui.add_head_html("""
    <style>
        @keyframes listening-pulse {
            0%, 100% {
                opacity: 1;
                transform: scale(1);
            }
            50% {
                opacity: 0.3;
                transform: scale(0.75);
            }
        }

        .listening-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #16A37A;
            animation: listening-pulse 1.5s ease-in-out infinite;
        }
    </style>
""")

    # Page styling
    ui.add_head_html("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            html,
            body,
            .q-body--standard,
            .q-card,
            .q-btn,
            .q-field,
            .q-page {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }

            .q-icon,
            .material-icons,
            .material-icons-outlined {
                font-family: 'Material Icons' !important;
            }
        </style>
        """)

    ui.query('body').style(
    'background-color: #EAF2FA; '
    'color: #172B4D; '
)
    # Main dashboard container
    with ui.column().classes('w-full max-w-7xl mx-auto p-6 gap-6'):

        # Header
        with ui.row().classes('w-full items-center justify-between'):

            # Logo and branding
            with ui.row().classes('items-center gap-3'):
                with ui.element('div').classes(
                        'w-14 h-14 rounded-2xl flex items-center justify-center'
                    ).style('background-color: #192B49;'):
                        ui.icon('security').classes(
                            'text-4xl text-white'
                        )

                with ui.column().classes('gap-0'):
                    ui.label('SCAM GUARDIAN').classes(
                        'text-2xl font-bold'
                    ).style('color: #101D35;')

                    ui.label('INTELLIGENT CALL PROTECTION').classes(
                        'text-xs font-bold tracking-widest'
                    ).style('color: #278CB8;')

            # Status and simulator controls
            with ui.row().classes('items-center gap-4'):
                with ui.row().classes(
                    'items-center gap-2 px-4 py-2 rounded-full'
                ).style('background-color: #DDF4EB;'):

                    ui.element('span').classes('listening-dot')

                    ui.label('LISTENING').classes(
                        'font-bold text-sm'
                    ).style('color: #137A5B;')

                ui.button(
                    'Simulate Scam Call',
                    on_click=simulate_call
                ).props('color=primary')
                ui.button(
                    'Reset Call',
                    on_click=reset_call
                ).props('color=negative')

        ui.separator()

        # First row: Transcript and Risk
        with ui.row().classes('w-full items-stretch gap-6 flex-nowrap'):

            # Live transcript
            with ui.card().classes('flex-1 min-w-0 rounded-2xl p-2 shadow-sm'):
                ui.label('LIVE TRANSCRIPT').classes(
                    'text-lg font-bold'
                )

                transcript_display = ui.column().classes('w-full gap-2')

            # Scam risk
            with ui.card().classes('flex-1 min-w-0 rounded-2xl p-2 shadow-sm'):
                ui.label('SCAM RISK').classes(
                    'text-lg font-bold'
                ).style('color: #101D35;')

                with ui.row().classes('w-full items-center gap-6'):

                    # Circular risk gauge
                    risk_gauge = ui.circular_progress(
                        value=0,
                        show_value=False
                    ).props(
                        'size=160px color=primary track-color=grey-3'
                    )

                    # Risk percentage and description
                    with ui.column().classes('gap-2'):
                        risk_display = ui.label('0%').classes(
                            'text-5xl font-bold'
                        ).style('color: #16A37A;')

                        risk_message = ui.label(
                            'No significant risk detected'
                        ).classes('text-gray-500')

        # Second row: Tactics and Advice
        with ui.row().classes('w-full items-stretch gap-6 flex-nowrap'):

            # Detected tactics
            with ui.card().classes('flex-1 min-w-0 rounded-2xl p-2 shadow-sm'):
                ui.label('DETECTED TACTICS').classes(
                    'text-lg font-bold'
                )

                tactics_display = ui.column().classes('w-full gap-2')

            # Guardian advice
            with ui.card().classes('flex-1 min-w-0 rounded-2xl p-2 shadow-sm'):
                ui.label('GUARDIAN ADVICE').classes(
                    'text-lg font-bold'
                )

                advice_display = ui.label(
                        'Guardian is listening.'
                    ).classes('text-gray-500')

        # Trusted contact
        with ui.card().classes('w-full rounded-2xl p-2 shadow-sm'):
            ui.label('TRUSTED CONTACT').classes(
                'text-lg font-bold'
            )

            ui.label(
                'No trusted contact configured yet.'
            ).classes('text-gray-500')

            ui.label(
                'Family alerts will be sent to your trusted contact '
                'when a high-risk call is detected.'
            ).classes('text-gray-600')

        # Refresh dashboard with the latest transcript
    seen = {'alerts': state['alert_count']}

    def refresh_dashboard():
        # Show a pop-up if a new family alert was sent
        if state['alert_count'] > seen['alerts']:
            seen['alerts'] = state['alert_count']
            ui.notify(
                'Family alert sent to your trusted contact',
                type='warning',
                position='top',
                timeout=6000
            )

        # Update transcript
        transcript_display.clear()

        with transcript_display:
            if state['transcript']:
                for chunk in state['transcript']:

                    is_user = chunk.speaker.lower() in [
                        'you', 'user', 'recipient', 'me'
                    ]

                    # Message alignment
                    with ui.row().classes(
                        'w-full justify-end' if is_user
                        else 'w-full justify-start'
                    ):

                        with ui.column().classes(
                            'gap-1'
                        ).style('max-width: 80%;'):

                            # Speaker name
                            ui.label(
                                'YOU' if is_user else 'CALLER'
                            ).classes(
                                'text-xs font-bold tracking-wide'
                            ).style(
                                'color: #278CB8;'
                            )

                            # Message bubble
                            ui.label(chunk.text).classes(
                                    'text-base px-4 py-3 rounded-2xl'
                            ).style(
                                    'background-color: #087AFF; '
                                    'color: #FFFFFF;'
                                    if is_user else
                                    'background-color: #E5E9F0; '
                                    'color: #000000;'
                                )

                            # Actual message timestamp
                            ui.label(
                                chunk.timestamp.strftime('%H:%M:%S')
                            ).classes(
                                'text-xs text-gray-500'
                            )

            else:
                ui.label(
                    'Conversation will appear here...'
                ).classes('text-gray-500')
            # Update risk percentage
        risk = state['risk']

        risk_display.set_text(f'{risk}%')
        risk_gauge.set_value(risk / 100)

        # Update risk message and colour
        if risk >= 80:
            risk_message.set_text('High risk detected!')
            risk_display.style('color: #E05252;')
            risk_gauge.props('color=negative')

        elif risk >= 50:
            risk_message.set_text('Suspicious activity detected.')
            risk_display.style('color: #E9A23B;')
            risk_gauge.props('color=warning')

        else:
            risk_message.set_text('No significant risk detected.')
            risk_display.style('color: #16A37A;')
            risk_gauge.props('color=positive')
                # Update detected tactics
        tactics_display.clear()

        with tactics_display:
            if state['tactics']:
                for tactic in state['tactics']:
                    ui.label(f'• {tactic}')
            else:
                ui.label(
                    'No suspicious tactics detected yet.'
                ).classes('text-gray-500')

        # Update Guardian advice
        advice_display.set_text(state['message'])

    # Refresh every half second
    ui.timer(0.5, refresh_dashboard)
@ui.page('/phone')
def phone_page():
    ui.add_head_html("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            html,
            body,
            .q-body--standard,
            .q-card,
            .q-btn,
            .q-field,
            .q-page {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }

            .q-icon,
            .material-icons,
            .material-icons-outlined {
                font-family: 'Material Icons' !important;
            }
        </style>
        """)
    ui.query('body').style(
    'background-color: #EAF2FA; '
    'color: #172B4D; '
    )
    with ui.column().classes('w-full max-w-md mx-auto p-6 gap-6'):
        ui.label('SCAM GUARDIAN').classes('text-2xl font-bold')

        risk_display = ui.label().classes('text-4xl font-bold')
        warning_display = ui.label().classes('text-xl font-bold')
        details_display = ui.label().classes('text-lg')

        ui.button(
            'End Call',
            on_click=lambda: ui.notify(
                'Please end the call using your phone.'
            )
        ).classes('w-full').props('color=negative size=xl')

        ui.button(
            'Contact Trusted Person',
            on_click=lambda: ui.notify(
                'Trusted contact feature coming soon.'
            )
        ).classes('w-full').props('color=primary size=xl')

    def refresh_phone():
        risk = state['risk']

        risk_display.set_text(f'{risk}% RISK')

        if risk >= 80:
            warning_display.set_text('High risk! This call may be a scam.')
            risk_display.style('color: #B54708;')
        elif risk >= 50:
            warning_display.set_text('Suspicious activity detected.')
            risk_display.style('color: #B54708;')
        else:
            warning_display.set_text('No significant risk detected.')
            risk_display.style('color: #0F5E63;')

        details_display.set_text(state['message'])

    ui.timer(0.5, refresh_phone)


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(host='0.0.0.0', port=8080)