---
id: 39
title: "An Audio Clip’s Properties as Displayed in the Clip View."
chapter: 39
---
# 39 An Audio Clip’s Properties as Displayed in the Clip View.

An Audio Clip’s Properties as Displayed in the Clip View.

Many powerful manipulations arise from Live’s warping capabilities. Warping means changing the
speed of sample playback independently from the pitch so as to match the song tempo. The tempo
can be adjusted on the fly in the Control Bar’s Tempo field.

The Control Bar’s Tempo Field.

The most elementary use of this technique, and one that usually requires no manual setup, is
synchronizing sample loops to the chosen tempo. Live’s Auto-Warp algorithm actually makes it easy
to line up any sample with the song tempo, such as a recording of a drunken jazz band’s
performance. It is also possible to radically change the sonic signature of a sound using extreme warp
settings.

3.10 MIDI Clips and MIDI Files

A MIDI clip contains musical material in the form of MIDI notes and controller envelopes. When MIDI
is imported from a MIDI file, the data gets incorporated into the Live Set, and the original file is not
referenced thereafter. In Live’s browser, a MIDI file appears with a special icon, and with the .mid file
extension.

A MIDI File in the Browser.

A MIDI clip’s contents can be accessed and edited via the Clip View, for instance to change a melody
or create a drum pattern.

A MIDI Clip’s Properties as Displayed in the Clip View.

Aside from recording incoming MIDI signals from external devices, Live also allows you to add MIDI
notes to clips through Draw Mode, MIDI Tools or audio-to-MIDI converters.

3.11 Devices

A track can contain not only clips but also a chain of devices for processing signals. Double-clicking a
track’s title bar brings up the Device View, which shows the track’s device chain.

The Device View Displaying a MIDI Track’s Device Chain.

Devices that receive and deliver audio signals are called audio effects. Audio effects are the only type
of device that fits in an audio track or a return track. However, two more types of devices are
available for use in MIDI tracks: MIDI effects and instruments.

Live’s built-in audio effects, MIDI effects, and instruments are available from the browser. You can add
devices to tracks by dragging them from the browser into the Device View, or dragging them onto a
Session or Arrangement track. You can also load instruments and effects into a track by selecting them
in the browser and pressing Enter .

Live’s Built-in Devices Are Available from the Browser.

You can also use plug-in devices in Live. VST and Audio Units (macOS only) plug-ins are available
from the browser’s Plug-Ins label.

Plug-In Devices Are Available from the Browser’s Plug-Ins Label.

3.12 Clip and Device View

The Clip View is where you can set and adjust clip properties such as start or end points, looping, or
scale settings. When in the Session View, you can also access extended clip properties such as follow
actions.

The Clip View

When working with audio clips, the Clip View allows you to access warping controls and audio
transformation tools.

When working with MIDI clips, the Clip View includes pitch and time utilities, as well as MIDI
Transformation and Generative tools.

The Device View shows a list of the devices currently loaded on a selected track. MIDI tracks can have
MIDI effects, instruments, and audio effects loaded. Audio, group, and return tracks can have audio
effects loaded.

The Device View.

The Clip View and Device View can be stacked, which lets you view them at the same time. To do this,
use the triangle toggles next to the Clip View and Device View Selectors located to the left of the
Mixer View toggle in the bottom-right corner of Live. You can also use the keyboard shortcuts Ctrl
Alt

3 (Mac) for showing the Clip View and Ctrl

Option

Alt

3 (Win) / Cmd
Option

(Win) / Cmd

4 (Mac) for showing the Device View.

Stacked Clip and Device View.

3.13 Scale Awareness

Live’s scale options let you set any clip to a scale of your choice, and can also be used to apply
scales across Live’s effects and devices. Once you activate Scale Mode for a given clip, effect, or
device, it becomes scale aware.

Scale awareness for clips can be enabled via the Scale Mode toggle in the Control Bar or directly
within the Clip View. A root key and scale type can be selected using the Root Note and Scale Name
choosers next to the Scale Mode toggle. Scale settings apply to a selected clip or, if no clip is
selected, to any subsequently created clips.

The Scale Mode Toggle and Scale Choosers in the Clip View.

The Scale Mode controls in the Control Bar reflect the current scale settings of any selected clip. These
controls can also be used to turn Scale Mode on/off or to set the same scale for multiple selected
clips.

Scale Options in the Control Bar.

In the Clip View, when Scale Mode is enabled, the Fold to Scale and Highlight Scale options will
appear in the MIDI Note Editor. When Fold to Scale is on, only the key tracks that belong to notes of
the scale will be displayed in the editor. When Highlight Scale is enabled, the key tracks that belong
to notes of the scale will be highlighted in purple, which is the color that signifies scale awareness
across Live.

When a scale is active, any pitch-related parameters in MIDI Tools and the Pitch and Time Utilities
panel will also use the selected scale.

Live’s Arpeggiator, Chord, Pitch, Random, and Scale MIDI effects include the Use Current Scale
toggle in their device title bars. When switched on, a clip’s current scale will be applied and pitch-
based device parameters will be adjustable in scale degrees rather than in semitones.

Scale awareness can also be enabled for Auto Shift’s Quantizer and for Meld’s oscillators and filters.

3.14 The Mixer

Consider an audio clip playing in an audio track. The audio signal from the clip reaches the leftmost
device in the chain. This device processes (changes) the signal and feeds the result into the next
device, and so on. The number of devices per track is theoretically unlimited. In practice, the
computer’s processing power imposes a limit on the number of devices you can use at the same time,
a topic that deserves separate discussion. Note that the signal connections between audio devices
are always stereo, but the software’s inputs and outputs can be configured to be mono in the Audio
Settings.

When the signal has passed through the device chain, it ends up in Live’s mixer. As the Session and
Arrangement share the same set of tracks, they also share the mixer. The mixer can be shown in both
views for convenience.

The Live Mixer in the Arrangement View.

To optimize the screen layout, the individual mixer sections can be shown or hidden using the Mixer
Controls entries in the View menu or the options in the Mixer Config Menu in the bottom right corner
of Live’s window.

The Mixer Config Menu Options.

The mixer has controls for volume, pan position and sends, which determine how much of a track’s
output feeds the associated return track’s input. Return tracks only contain effects, and not clips. Via
their sends, all tracks can feed a part of their signal into a return track and share its effects.

The mixer also includes a crossfader, which can create smooth transitions between clips playing on
different tracks. Live’s crossfader works like a typical DJ mixer crossfader, with the exception that it
allows crossfading not just two but any number of tracks — including the returns.

The Crossfader and Track Crossfader Assign Buttons.

Consider a MIDI track playing a clip. The MIDI signal from the clip is fed into the track’s device chain.
There, it is first processed by any number of MIDI effects. A MIDI effect receives and delivers MIDI
signals. The last MIDI effect in the chain is followed by an instrument, which receives MIDI and outputs
audio. Following the instrument, there can be any number of audio effects — as in an audio track.

A MIDI Effect, an Instrument and Some Audio Effects in a MIDI Track.

If a MIDI track has no instrument (and no audio effects), then the track’s output is a plain MIDI signal,
which has to be sent somewhere else to be converted into audio. In this case, the track’s mix and send
controls disappear from the mixer.

The Mixer for a MIDI Track without an Instrument.

3.15 Presets and Racks

Every Live device can store and retrieve particular sets of parameter values as presets. As presets are
stored independently from Live Sets, new presets become part of your User Library that any project
can draw from.

Live’s Instrument, Drum and Effect Racks allow saving combinations of devices and their settings as a
single preset. This feature makes it possible to put together powerful multi-device creations, effectively
adding all the capabilities of Live’s MIDI and audio effects to the built-in instruments.

3.16 Routing

All tracks deliver signals, either audio or MIDI. The targets for these signals are set up in the mixer’s
In/Out section, which contains signal source and destination choosers for every track. The In/Out

section, accessible via the In/Out option in the Mixer Controls submenu of the View menu, is Live’s
“patchbay.“ Its routing options enable valuable creative and technical methods such as resampling,
submixing, layering of synths, complex effects setups, and more.

Track Routing Is Set up Using the In/Out Section.

Signals from the tracks can be sent out of Live via the computer’s audio and MIDI interfaces, to
different programs that are connected to tracks or devices within Live. Tracks can also be combined
into a group track which serves as a submixer for the selected tracks.

Likewise, a track can be set up to receive an input signal to be played through the track’s devices.
Again, tracks can receive their input from outside of Live or from another track or device in Live. The
monitoring controls regulate the conditions under which the input signal is heard through the track.

It is also possible to route signals to external hardware devices from within a track’s device chain, by
using the External Audio Effect and External Instrument devices.

3.17 Recording New Clips

Audio tracks and MIDI tracks can record their input signal and thereby create new clips. Recording is
enabled on a track by pressing its Arm button. With multiple tracks selected, pressing any of their Arm
buttons will arm all of them. You can also hold down the Ctrl (Win) / Cmd (Mac) modifier when
clicking the Arm buttons to arm several tracks at once. If the Exclusive Arm option is enabled in the
Record, Warp & Launch Settings, inserting an instrument into a new or empty MIDI track will
automatically arm the track. When the Control Bar’s Arrangement Record button is on, every armed
track records its input signal into the Arrangement. Every take yields a new clip per track.

Track Arm Buttons.

It is also possible to record into Session View slots on the fly. This technique is very useful for the
jamming musician, as Session recording does not require stopping the music. Clicking the Session
Record button records a new clip in the selected Session scene in all armed tracks.

The Control Bar’s Session Record Button.

Clicking the Session Record button again stops the recording and launches the new clips. As these
actions are subject to real-time launch quantization, the resulting clips can be automatically cut to the
beat.

The Control Bar’s Quantization Chooser.

Session recording in conjunction with overdubbing and Record Quantization is the method of choice
for creating drum patterns, which are built up by successively adding notes to the pattern while it
plays in a loop. It only takes a MIDI keyboard (or the computer keyboard) and a MIDI track with
Live’s Impulse percussion instrument to do this.

3.18 Automation Envelopes

Often, when working with Live’s mixer and effects, you will want the adjustments made to the controls’
values to become part of the Set. The changes to a control’s value that happen across the
Arrangement timeline or Session clip are called automation; a control whose value changes over time
is automated. Automation is represented by breakpoint envelopes, which can be drawn, edited and
recorded in real-time.

Automated Parameters in the Arrangement View.

Practically all mixer and effect controls in Live can be automated, even the song tempo. Recording
automation is straightforward: all changes of a control that occur while the Control Bar’s Automation
Arm and Arrangement Record buttons are on become automation in the Arrangement View.
Automation is recorded to Session View clips if controls are adjusted while recording with the
Automation Arm button enabled.

Changing an automated control’s value while not recording is similar to launching a Session clip while
the Arrangement is playing: It deactivates the control’s automation (in favor of the new control setting).
The control will stop tracking its automation and continue using the new value until the Re-Enable
Automation button is pressed or a Session clip that contains automation is launched.

3.19 Clip Envelopes

Envelopes can be found in both tracks and clips. Clip envelopes are used to automate or modulate
device and mixer controls. Audio clips have additional clip envelopes to influence the clip’s pitch,
volume and more; these can be used to change the melody and rhythm of recorded audio. MIDI clips
have extra clip envelopes to represent MIDI controller data. Clip envelopes can be unlinked from the
clip to give them independent loop settings, so that larger movements (like fade-outs) or smaller
gestures (like an arpeggio) can be superimposed onto the clip’s material.

An Envelope for Clip Transposition.

3.20 Undo History

Undo History displays a list of actions taken since opening a Set and lets you revert or reapply them
as needed. Actions are listed from newest at the top to oldest at the bottom, and each one can be
reverted when deselected or reapplied when selected.

To open the list, select Undo History from the View menu or use Ctrl
Option

Z (Mac).

Alt

Z (Win) / Cmd

Undo History.

To restore an action, click on an entry in the list or select an entry with your keyboard and press Enter.
When an action is selected, all of the actions that followed it (i.e. those listed above the selected
action in the Undo History view) are greyed out, indicating that they have been undone. All of the
actions that precede the selected action (i.e. those listed below it in the view) remain active, indicating
that their changes still apply. This workflow makes it easy to reverse or recover multiple actions at once
instead of undoing or redoing each step individually.

Note that the Undo History view is cleared whenever you open a Set, be it a new Set when opening
Live or an existing saved Set. Creating or opening a Set is treated as the first action in the Undo
History view and cannot be undone.

3.21 MIDI and Key Remote

To liberate the musician from the mouse, most of Live’s controls can be remote-controlled via an
external MIDI controller. Remote mappings are established in MIDI Map Mode, which is engaged by
pressing the MIDI switch in the Control Bar.

In this mode, you can click on any mixer or effect control, and then assign it to a controller simply by
sending the desired MIDI message (for example, by turning a knob on your MIDI control box). Your
assignments take effect immediately after you leave MIDI Map Mode. Session clips can be mapped
to a MIDI key or even a keyboard range for chromatic playing.

MIDI keys and controllers that have been mapped to Live’s controls are not available for recording
via MIDI tracks. These messages are filtered out before the incoming MIDI is passed on to the MIDI
tracks.

The Key/MIDI Map Controls.

Session clips, switches, buttons and radio buttons can be mapped to computer keyboard keys as well.
This happens in Key Map Mode, which works just like MIDI Map Mode.

Live offers, in addition to this general purpose mapping technique, dedicated support for Ableton Push
1, Push 2, and Push 3.

3.22 Saving and Exporting

Saving a Live Set saves everything it contains, including all clips, their positions and settings, and
settings for devices and controls. An audio clip can, however, lose the reference to its corresponding
sample if the sample is moved or deleted from disk. The links between samples and their clips can be
preserved with a special command, Collect All and Save, which makes a copy of each sample and
stores it in a project folder along with the Live Set.

A separate Save button in the Clip Title Bar of an audio clip can be used to save a set of default clip
settings along with the sample, so that each time the sample is dragged into the program, it will be
automatically loaded with these settings. This is especially useful if you have specific warp settings for
a clip that you want to use in multiple Live Sets.

Exporting audio from Live can be done from both the Session and Arrangement Views by selecting
R (Win) / Cmd
‘Export Audio/Video’ from the File menu or by using the shortcut Ctrl

Shift

Shift

R (Mac). By default, Live will export the audio coming through on the Main output as an

audio file of your specifications via the Export Audio/Video dialog options.

Live can also export individual MIDI clips as MIDI files.

Exporting and saving material for later use in Live can be done very conveniently with the Live Clip
format. Session View clips can be dragged back out of a Live Set to the User Library, and thereby
exported to the disk as Live Clips.

A Live Clip in the Browser.

Live Clips are a very powerful way of storing ideas, as they save not only the clip’s Clip View settings,
but also the corresponding track’s instruments and effects chain. Live Clips in the browser can be
previewed and added to any open Live Set just like sample files. Once loaded in a Live Set, they are
restored with the original envelope and device settings.

Using Live Clips, you can build your own personalized library of:

•

•
•
•

MIDI sequences with matching instruments and effects, e.g., a MIDI drum pattern with the
associated Impulse and effects settings;
Different regions or loops referencing the same source file;
Variations of a sample loop created by applying Warp Markers, clip envelopes and effects;
Ideas that may not fit your current project but could be useful in the future.

4. Working with the Browser

Live’s browser is the place where you interact with your library of musical assets: the Core Library of
sounds included with the program, any additional sounds you’ve installed via Live Packs, presets,
samples you’ve saved, built-in and third-party devices, and any folders on your hard drive that
contain samples, tracks, etc. Additionally, you can access files from Ableton Cloud and Push in
Standalone Mode via the browser’s Places section.

The browser contains several sections and controls for searching, filtering, browsing, and previewing
content. These include the search bar, sidebar, filters, content pane, and other tools.

The Browser’s Layout.

1.

The browser’s sidebar contains the Collections, Library, and Places sections and their
associated labels.

2.

The Browse Back and Browse Forward buttons can be used to access the browser’s previous
search or navigation states.

3.

The search field helps you find browser items and tagged content.

4.

The Show/Hide Filter toggle can be used to show or hide the browser’s filters, while the Filter
View menu can be used to specify which filter groups are visible in the Filter View, and to
toggle the Tag Editor, Quick Tags, and Auto Tags.

5.

The Filter View contains a set of filter groups with associated tags which you can use to search
for items in your library.
