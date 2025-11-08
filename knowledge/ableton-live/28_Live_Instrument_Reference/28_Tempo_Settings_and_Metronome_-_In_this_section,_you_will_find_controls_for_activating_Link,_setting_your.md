---
id: 28
title: "Tempo Settings and Metronome - In this section, you will find controls for activating Link, setting your"
chapter: 28
---
# 28 Tempo Settings and Metronome - In this section, you will find controls for activating Link, setting your

Tempo Settings and Metronome - In this section, you will find controls for activating Link, setting your
Set’s tempo and time signature, customizing the metronome, and toggling Tempo Follower on or off.

Scale Settings - This section reflects the scale settings of the currently selected clip. Changes made to
scale settings in this section are applied to the currently selected clip/clip slot and to any subsequently
created clips or selected clip slots.

Follow and Arrangement Position - In this section, you can turn Follow on or off, as well as view and
adjust the current Arrangement position.

Transport Controls - This section contains controls for starting or stopping playback, and for starting
Arrangement recording.

Automation and Capture MIDI - This section contains controls for customizing MIDI overdub settings,
arming automation, re-enabling automation for currently overriden parameters, capturing MIDI, and
starting Session recording.

Arrangement Loop Settings - This section lets you activate and configure the Arrangement loop and
the recording punch-in and punch-out points.

MIDI and CPU Settings - This section lets you activate Draw Mode, enable the Computer MIDI
Keyboard, turn Key and MIDI map modes on or off, change the project sample rate, and monitor
CPU usage.

View Selector - This section contains a toggle that lets you switch between the Session and
Arrangement View.

3.2 The Status Bar

The Status Bar displays useful information like error messages or updates about available releases
(when Automatic Updates are enabled in the Licenses & Updates Settings).

The Status Bar.

When working in the MIDI Note Editor, the Status Bar also provides helpful details about a selected
note’s location, pitch, velocity, and probability. When hovering over an insert marker in the Session or
Arrangement View, the Status Bar displays the marker’s precise location.

3.3 The Browser

Live’s browser is the place where you interact with your library of musical assets: the Core Library of
sounds that are installed with the program, any additional sounds you’ve installed via Live Packs,
presets and samples you’ve saved, built-in and third-party devices, your Sets saved in Ableton Cloud,
your files stored on Push, and any folders that you’ve added manually.

The Browser.

You can show or hide the browser using the dedicated Show/Hide Browser toggle in the Control Bar
5 (Win) / Cmd
or by using the shortcut Ctrl
options in the Browser Config Menu to display additional sections or expand the browser to full
height.

5 (Mac). You can also use the

Option

Alt

3.4 Sound Similarity

Live comes with sound similarity recognition which is used in two features: Similarity Search and
Similar Sample Swapping. Similarity Search helps you find sounds similar to a reference file by
comparing the reference to the items in the Core Library and the User Library. Similarity Search works
with samples up to 60 seconds long, instrument presets, and drum presets. It can also be used in
conjunction with Live’s Similar Sample Swapping feature to replace sample files with other similar
sounds in Drum Rack, Simpler, or Drum Sampler.

A Show Similar Files icon is displayed next to compatible files that have been selected in the browser.

The Show Similar Files Icon Next to a Sample.

Clicking on the icon will bring up a list of sounds similar to the reference file. You can also right-click
an item and select Show Similar Files or use the Ctrl
(Mac) shortcut to view this list. The reference file will be shown in the search field and all relevant
similar sounding items will be listed below it, ordered from most to least similar.

F (Win) / Cmd

Shift

Shift

5F

Similarity Search Results.

When saving custom User Labels based on a list of Similarity Search results, the sound file that the
search was based on is automatically shown at the top of the list.

Sound content needs to be analyzed in order for sound similarity features to work. The sound analysis
is performed in the background whenever Live discovers new user audio files. The status of Live’s
similarity sound analysis is displayed in the Status Bar when background scanning and analysis are in
progress, and a Pause button next to the analysis state can be used to stop this process at any time.
Note that the Core Library content is pre-analyzed.

3.5 Live Sets

The type of document that you create and work on in Live is called a Live Set. A Live Set resides in a
Live Project — a folder that collects related materials. Once the Project folder is saved, the Set can be
opened again using the File menu’s Open command.

A Live Set in the Browser.

The Live Project folder and related files belonging to the currently open Live Set are also accessible via
the Current Project label in Live’s Places.

3.6 Arrangement and Session

The basic musical building blocks of Live are called clips. A clip is a piece of musical material: a
melody, a drum pattern, a bassline or a complete song. Live allows you to record and alter clips, and
to create larger musical structures from them: songs, scores, remixes, DJ sets or stage shows.

You can work with clips in two views: the Arrangement, which is a layout of clips along a musical and
linear timeline; and the Session, which is a real-time-oriented “launching base” for clips. Every

Session clip has its own play button that allows launching the clip at any time and in any order. Each
clip’s behavior upon launch can be precisely specified through a number of settings.

Clips in the Arrangement View (Left) and in the Session View (Right).

The Arrangement is accessed via the Arrangement View and the Session via the Session View.

If you’re using Live in a single window, you can toggle between the two views using the computer’s
Tab key or their respective view controls in the top right corner of Live’s window. If you’re using two
windows, pressing Tab will swap the Session and Arrangement from one window to the other. Note
that if the ‘Use Tab Key to Navigate’ option is enabled in the Display & Input Settings, pressing Tab
will not switch between Arrangement and Session View. However, you can switch between the views
2 (Win) /
using the shortcuts Alt
2 (Mac) for Arrangement View. You can also switch between the views at any time using
Option

1 (Mac) for Session View and Alt

1 (Win) / Option

their Navigate menu entries.

The Arrangement and Session View Controls.

Because the two views have distinct applications, they each hold individual collections of clips.
However, it is important to understand that when you switch between the views during playback or
recording, only the UI is affected and not the currently playing clips.

The Arrangement View and the Session View interact in useful ways. One can, for instance, improvise
with Session clips and record a log of the improvisation into the Arrangement for further refinement.
This works because Arrangement and Session are connected via tracks.

3.7 Tracks

Tracks host clips and also manage the flow of signals, as well as the creation of new clips through
recording, sound synthesis, effects processing and mixing.

A Track in the Arrangement View.

The Session and Arrangement share the same set of tracks. In the Session View, the tracks are laid out
in columns, while in the Arrangement View they are stacked vertically, with time moving from left to
right.

A track can only play one clip at a time. Therefore, one usually places clips that should play
alternatively in the same Session View column, and spreads out clips that should play together across
tracks in rows, or what we call scenes.

A Scene in the Session View.

At any one time, a track can be playing either a Session clip or an Arrangement clip, but never both.
Session clips take precedence. When a Session clip is launched, the currently playing clip stops in
favor of playing the newly-launched clip. In particular, if an Arrangement clip is playing on the track,
it will stop so that the Session clip can be played instead — even as the other tracks continue to play
Arrangement clips. The Arrangement clips in the track where the Session clip was launched will not
resume playback until you manually restart it using the Back to Arrangement button.

The Back to Arrangement button can be found in the Main track in the Session View and at the top-
right of the scrub area in the Arrangement View. This button lights up to indicate that one or more
tracks are currently not playing the Arrangement, but are playing a clip from the Session instead.

The Back to Arrangement Button in the Session View.

The Back to Arrangement Button in the Arrangement View.

You can click this button to make all tracks go back to playing the Arrangement. Each track in the
Arrangement View also has its own Back to Arrangement button, allowing you to resume
Arrangement playback of only certain tracks.

A Single Track’s Back to Arrangement Button.

It is also possible to capture the current Session state into the Arrangement by activating the
Arrangement Record button from the Session View.

The Arrangement Record Button.

Recording into the Arrangement tracks allows you to create multiple takes for a clip and then put them
together into a composite track.

You can also link tracks together to perform the same operations on multiple tracks simultaneously.

Creating a Fade in Two Linked Tracks.

3.8 Audio and MIDI

Live deals with two types of signals: audio and MIDI. In the digital world, an audio signal is a series of
numbers that approximates a continuous waveform. The signal can originate from various sources,
including audio from a microphone, a sound synthesized or sampled through software, or a signal
delivered to a loudspeaker. A MIDI signal is a sequence of commands, such as “now play a C4 at
mezzo piano.“ MIDI is a symbolic representation of musical material, one that is closer to a written
score than to an audio recording. MIDI signals are generated by hardware input devices such as
MIDI or USB keyboards or software devices.

It takes an instrument to convert MIDI signals into audio signals that can actually be heard. Some
instruments, such as Live’s Simpler, are for chromatic playing of one sound via the keyboard. Other
instruments, such as Live’s Impulse, have a different percussion sound assigned to each keyboard key.

Audio signals are recorded and played back using audio tracks, and MIDI signals are recorded and
played back using MIDI tracks. The two track types have their own corresponding clip types. Audio
clips cannot be added to MIDI tracks and vice versa.

You can find more information about inserting, reordering, and deleting audio and MIDI tracks in the
Audio and MIDI Tracks section of the Mixing chapter.

3.9 Audio Clips and Samples

An audio clip contains a reference to a sample (also known as a “sound file“ or “audio file“) or a
compressed sample (such as an MP3 file). The clip contains information that instructs Live where on
the computer’s drives to find the sample, what part of the sample to play and how to play it.

When a sample is dragged in from Live’s built-in browser, Live automatically creates a clip to play that
sample. Prior to dragging in a sample, one can audition or preview it directly in the browser. When
the Browser File Preview button with the headphones icon is toggled on, the preview starts
automatically once the sample is selected.

A Selected Sample with Audio Preview in the Browser.

Live offers many options for playing samples in exciting new ways, allowing you to create an
abundance of new sounds without actually changing the original sample — all the changes are
computed in real time, while the sample is played. The respective settings can be found in the Clip
View, which opens when a clip is double-clicked.
