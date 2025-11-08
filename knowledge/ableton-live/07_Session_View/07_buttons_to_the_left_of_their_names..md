---
id: 07
title: "buttons to the left of their names."
chapter: 07
---
# 7 buttons to the left of their names.

7.

 buttons to the left of their names.

Make sure that Live’s Arrangement View is visible. If you’re using Live on a single monitor, your
computer keyboard’s Tab key will toggle between the Session View and Arrangement View.
Drag a QuickTime movie from Live’s browser and drop it into an audio track in the Arrangement
View. The Video Window will appear to display the video component of the movie file.
Remember that you can move this window to any convenient location on the screen.
Now that the video clip is loaded, drag an audio clip into the Arrangement View’s drop area. A
new track will automatically be created for it. Unfold both tracks so you can see their contents
by clicking the
Double-click on the video clip’s title bar to view it in the Clip View. In the Audio tab/panel,
make sure that the Warp button is enabled. Warped clips in the Arrangement View can be set
as tempo leader or follower. We want the Leader/Follower switch set to Leader, which will
force the rest of the clips in the Live Set to adapt to the video clip’s tempo (i.e., its normal
playback rate).
Now add Warp Markers to the video clip, and adjust them to your liking. The locations of the
Warp Markers define the synchronizing points between our music and our video. Notice how
the video clip’s waveform in the Arrangement View updates to reflect your changes as you
make them.
If desired, enable the Arrangement Loop to focus on a specific section of the composition.
When you have finished, choose the Export Audio/Video command from Live’s File menu. All
of your audio will be mixed down and saved as a single audio file. You can also export your
video file using this command.

25.4 Video Trimming Tricks

Commonly, composers receive movie files with a few seconds of blank space before the “real“
beginning of the action. This pre-roll (“two-beep“) serves as a sync reference for the mixing engineer,
who expects that the composer’s audio files will also include the same pre-roll. While working on
music, however, the pre-roll is in the composer’s way: It would be more natural for the movie action to
start at song time 1.1.1 and SMPTE time 00:00:00:00. This can be accommodated by trimming video
clips, as follows.

1.

First, we drop a movie file at the start of the Arrangement (1.1.1).

A Video Clip at the Start of the Arrangement.

1.

Next, we double-click on the video clip’s title bar to display its contents in the Clip View. There,
we drag the Start Marker to the right so the video clip starts at the beginning of the action.

Dragging the Start Marker behind the Pre-Roll.

1.

2.

Now, both the action and the music to be composed start at 1.1.1 / 00.00.00.00. Once the
music is done and ready to be rendered to disk, we need to bring back the pre-roll:
In the Arrangement View, we select all materials (Edit menu/Select All), then drag the entire
composition a few seconds to the right:

The Video Clip and the Final Clip of Music.

1.

Now, we click on the video clip’s title bar (to deselect everything else), then drag the video
clip’s left edge to the left as far as possible to reveal the pre-roll again.

The Video Clip with Pre-Roll Restored.

The Export Audio/Video command, by default, creates sample files as long as the Arrangement
selection; as the video clip is still selected, the exported sample file will have the exact same duration
as the original movie file, including the pre-roll.

26. Live Audio Effect Reference

Live comes with a selection of custom-designed, built-in audio effects. These effects range from
essential utilities like EQs, compressors, and filters to creative shaping tools such as delays, reverbs,
and saturators, among others.

To learn the basics of using effects in Live, check out the Working with Instruments and Effects chapter.

Note that different editions of Live have different feature sets, so some audio effects covered in this
reference may not be available in all editions.

26.1 Amp

The Amp Effect.

Amp is an effect that emulates the sound and character of seven classic guitar amplifiers. Developed
in collaboration with Softube, Amp uses physical modelling technology to provide a range of
authentic and usable amplifier tones, with a simple and consistent set of controls.

There are seven amp models to choose from:

•

•
•

•

•
•

•

Clean is based on the ”Brilliant” channel of a classic amp from the ’60s. This amp was widely
used by guitarists of the British Invasion.
Boost is based on the ”Tremolo” channel of the same amp, and is great for edgy rock riffs.
Blues is based on a ’70s-era guitar amp with a bright character. This classic amp is popular
with country, rock and blues guitarists.
Rock is modeled after a classic 45 watt amp from the ’60s. This is perhaps the best known rock
amp of all time.
Lead is based on the ”Modern” channel of a high-gain amp popular with metal guitarists.
Heavy is based on the ”Vintage” channel of the same amp and is also ideal for metal and
grunge sounds.
Bass is modeled after a rare PA from the ’70s which has become popular with bass players due
to its strong low end and ”fuzz” at high volumes.

Although the real-world versions of these amplifiers all have unique parameters, Live’s Amp effect uses
the same set of controls for each model. This makes it very easy to quickly change the overall
character of your sound without having to make numerous adjustments.

Gain adjusts the level of input to the preamplifier, while Volume adjusts the output stage of the power
amplifier. Although Gain and Volume work together to determine Amp’s overall level, Gain is the
primary control for the distortion amount. Higher Gain settings result in a more distorted sound. When
using the Blues, Heavy and Bass models, high Volume levels can also add considerable distortion.

The Bass, Middle and Treble knobs are EQ controls that adjust the timbre of the sound. As on a real-
world amplifier, Amp’s EQ parameters interact with each other — and with the rest of Amp’s
parameters — in non-linear and sometimes unpredictable ways. For example, increasing EQ levels
can, in some cases, also increase the amount of distortion.

Presence is an additional tone control for mid/high frequencies in the power amp stage. Its influence
on the sound varies considerably depending on the amp model used but can add (or subtract)
”edge” or ”crispness.”

The Output switch toggles between mono and stereo (Dual) processing. Note that in Dual mode, Amp
uses twice as much CPU.

The Dry/Wet control adjusts the balance between the processed and dry signals.

26.1.1 Amp Tips

Because Amp is modeled on real-world analog devices, its behavior can sometimes be difficult to
predict. Here are some tips on getting the most out of Amp:

26.1.1.1 Amps and Cabinets

Guitar amps are designed to be used with accompanying speaker cabinets. For this reason, Amp
comes with a companion effect called Cabinet which is designed to be used after Amp in a device

chain. If you’re looking for authenticity, we recommend this signal flow. But you can also achieve
interesting and exotic sounds by using Amp and Cabinet independently.

26.1.1.2 Electricity

The various circuits in guitar amps work with a continuous and fixed amount of electricity. For this
reason, turning up a particular parameter may inadvertently decrease the amount of available energy
somewhere else in the amp. This is particularly noticeable in the EQ controls. For example, turning up
Treble can reduce the level of bass and midrange frequencies. You may find that you need to carefully
adjust a number of seemingly unrelated parameters to get the results you want.

26.1.1.3 More than guitars

While Amp and Cabinet sound great with guitars, you can get very interesting results by feeding them
with drums, synthesizers or other sound sources. For example, try using Amp with Operator or Analog
to add analog grit to your digital sounds.

26.2 Auto Filter

The Auto Filter Effect.

The Auto Filter effect provides classic analog filter emulation. It can be modulated by an envelope
follower and/or an LFO to create moving filter effects. The envelope follower can track either the
filtered signal or an external sidechain source.

Auto Filter offers a variety of filter types including low-pass, high-pass, band-pass, notch, and a
special Morph filter. Each filter can be switched between 12 and 24 dB slopes as well as a selection
of analog-modeled circuit behaviors developed in conjunction with Cytomic that emulate hardware
filters found on some classic analog synthesizers.

The Clean circuit option is a high-quality, CPU-efficient design that is the same as the filters used in EQ
Eight. This is available for all of the filter types.

The OSR circuit option is a state-variable type with resonance limited by a unique hard-clipping
diode. This is modeled on the filters used in a somewhat rare British monosynth, and is available for all
filter types.

The MS2 circuit option uses a Sallen-Key design and soft clipping to limit resonance. It is modeled on
the filters used in a famous semi-modular Japanese monosynth and is available for the low-pass and
high-pass filters.

The SMP circuit is a custom design not based on any particular hardware. It shares characteristics of
both the MS2 and PRD circuits and is available for the low-pass and high-pass filters.

The PRD circuit uses a ladder design and has no explicit resonance limiting. It is modeled on the filters
used in a legacy dual-oscillator monosynth from the United States and is available for the low-pass
and high-pass filters.

The most important filter parameters are the typical synth controls Frequency and Resonance.
Frequency determines where in the harmonic spectrum the filter is applied; Resonance boosts
frequencies near that point.

When using the low-pass, high-pass, or band-pass filter with any circuit type besides Clean, there is
an additional Drive control that can be used to add gain or distortion to the signal before it enters the
filter.

The Morph filter has an additional Morph control which sweeps the filter type continuously from low-
pass to band-pass to high-pass to notch and back to low-pass.

You can quickly snap the Morph control to a low-pass, band-pass, high-pass, or notch setting via
dedicated options in the context menu of the Morph knob.

You can adjust Frequency and Resonance by clicking and dragging in the X-Y controller or via the
knobs. You can also click on the Freq and Res numeric displays and type in exact values.

When using the non-Clean circuit types, the Resonance control allows for self-oscillation. At
Resonance values above 100%, the filter will continue to ring indefinitely even after the input signal
has been stopped. The pitch of the self-oscillation depends on both the Frequency and Resonance
values.

The Envelope section controls how the envelope modulation affects the filter frequency. The Amount
control defines the extent to which the envelope affects the filter frequency, while the Attack control
sets how the envelope responds to rising input signals. Low Attack values cause a fast response to
input levels; high values integrate any changes gradually, creating a looser, slower response. Think of
it as adding inertia to the response.

Lower Release values cause the envelope to respond more quickly to falling input signals. Higher
values extend the envelope’s decay.

Normally, the signal being filtered and the input source that triggers the envelope follower are the
same signal. But by using sidechaining, it is possible to filter a signal based on the envelope of
another signal. To access the Sidechain parameters, unfold the Auto Filter window by toggling the
button in its title bar.

Auto Filter’s Sidechain Parameters.

Enabling this section with the Sidechain button allows you to select another track from the choosers
below. This causes the selected track’s signal to trigger the filter’s envelope follower, instead of the
signal that is actually being filtered.

The Gain knob adjusts the level of the external sidechain’s input, while the Dry/Wet knob allows you
to use a combination of sidechain and original signal as the envelope follower’s trigger. With Dry/
Wet at 100%, the envelope follower tracks the sidechain source exclusively. At 0%, the sidechain is
effectively bypassed. Note that increasing the gain does not increase the volume of the source signal
in the mix. The sidechain audio is only a trigger for the envelope follower and is never actually heard.

The Auto Filter also contains a Low Frequency Oscillator to modulate filter frequency in a periodic
fashion. The respective Amount control sets how much the LFO affects the filter. This can be used in
conjunction with or instead of the envelope follower.

The Rate control specifies the LFO speed. It can be set in terms of hertz, or synced to the song tempo,
allowing for controlled rhythmic filtering.

Available LFO waveform shapes are sine (creates smooth modulations with rounded peaks and
valleys), square, triangle, sawtooth up, sawtooth down, and sample and hold (generates random
positive and negative modulation values) in mono and stereo.

There are two LFOs, one for each stereo channel. The Phase and Offset controls define the relationship
between these two LFOs.

Phase keeps both LFOs at the same frequency, but can set the two LFO waveforms ”out of phase” with
each other, creating stereo movement. Set to ”180”, the LFO outputs are 180 degrees apart, so that
when one LFO reaches its peak, the other is at its minimum.

Spin detunes the two LFO speeds relative to each other. Each stereo channel is modulated at a
different frequency, as determined by the Spin amount.

For sample and hold (“S&H”), the Phase and Spin controls are not relevant and do not affect the
sound. Instead, the Auto Filter offers two kinds of sample and hold: The upper sample and hold type
available in the chooser provides independent random modulation generators for the left and right
channels (stereo), while the lower one modulates both channels with the same signal (mono).

The Quantize Beat control applies quantized modulation to the filter frequency. With Quantize Beat
off, frequency modulation follows the control source, e.g., the Envelope, LFO, or manually-adjusted
cutoff. Turning this feature on updates the filter modulation rhythmically with stepped changes that
track the tempo. The numbered buttons represent 16th notes, so, for example, selecting “4” as a beat
value produces a modulation change once per quarter note.

26.3 Auto Pan

The Auto Pan Effect.

Auto Pan offers LFO-driven manipulation of amplitude and panning for creating automatic panning,
tremolo and amplitude modulation, and beat-synchronized chopping effects.

Auto Pan’s LFOs modulate the amplitude of the left and right stereo channels with sine, triangle,
sawtooth down or random waveforms.

The Shape control pushes the waveform to its upper and lower limits, ”hardening” its shape. The
waveform can be set to ”Normal” or ”Invert” (use ”Invert” to, for example, create the saw up
waveform from the saw down waveform).

LFO speed is controlled with the Rate control, which can be set in terms of hertz. Rate can also be
synced to the song tempo.

Though both LFOs run at the same frequency, the Phase control lends the sound stereo movement by
offsetting their waveforms relative to each other. Set this to ”180”, and the LFOs will be perfectly out
of phase (180 degrees apart), so that when one reaches its peak, the other is at its minimum. Phase is
particularly effective for creating vibrato effects.

The Offset control shifts the start point of each LFO along its waveform.

The device’s influence on incoming signals is set with the Amount control.

26.4 Auto Shift

The Auto Shift Effect.

Auto Shift is a real-time pitch tracking and correction device with controls for vibrato, pitch shifting,
and formant shifting. Its design makes it especially well-suited for transforming vocals, though it can
be used with any monophonic audio signal. You can pitch correct audio using a defined scale or
using the MIDI notes from a separate track. Auto Shift also includes a built-in LFO, so you can
modulate incoming audio over time.

26.4.1 Input Section

Auto Shift’s Input Section.

Auto Shift can receive audio as well as MIDI input. The Input section lets you configure how incoming
signals are processed in the device.

The Input Pitch display shows the pitch of the incoming audio in notes and cents.

You can set the frequency range for the audio input using one of the three Pitch Range toggles. This
helps optimize the quality of the pitch estimation and correction. Use High for signals in a high
frequency range, Mid for signals in a mid frequency range, and Bass for signals in a low frequency
range. Each toggle has an LED that flashes when the incoming audio falls within its corresponding
range.

The Pitch Range LED Flashes to Indicate the Range for the Incoming Signal.

Note that each pitch range setting affects the device’s latency differently, so switching between
toggles changes the overall latency.

You can use the Input Gain slider to adjust the gain of the incoming signal from -24 to +24 dB.

The Latency Readout displays the device’s latency in milliseconds. Enabling Live Mode via the toggle
in the device’s title bar can help reduce latency, which is particularly useful for live performances.
However, slight glitches may occur during note onsets or rapid pitch changes in this mode.

Enable Live Mode to Reduce Latency.

26.4.1.1 MIDI Input

Auto Shift’s MIDI Input Panel.

Enabling MIDI input lets you use the notes from a separate MIDI track to pitch correct the incoming
audio instead of tuning it to a defined scale via the Quantizer.

The MIDI In toggle shows or hides the MIDI Input panel, which contains track routing and voice mode
settings.

Use the MIDI On toggle to activate or deactivate MIDI input. When enabled, the Quantizer tab is
replaced with the MIDI tab, where you can further shape the behavior of incoming MIDI notes.

The External Source chooser sets the MIDI sidechain source, i.e., the track used to send notes to Auto
Shift. The Tapping Point chooser lets you specify whether the MIDI sidechain is sent before or after any
MIDI effects that are in the source track’s device chain. Select Pre FX to bypass the effects on the track,
or select Post FX or Post Mixer to include them.

There are two voice mode toggles to choose from: Mono and Poly. Mono uses a single voice,
meaning that only one note can be used for the pitch correction at a time. You can use the Glide slider
to set the time that overlapping notes take to slide their pitch to the next incoming pitch. Poly can use
up to eight voices at once, making it ideal for harmonization. Use the Voice Count chooser to set the
maximum number of voices to 2, 4, or 8.

Note that when using MIDI input, Auto Shift will only produce sound when MIDI notes are received.

26.4.2 Quantizer Tab

Auto Shift’s Quantizer Tab.

The Quantizer corrects incoming audio according to the notes of a defined scale. In the Quantizer
tab, you can access controls for monitoring how the signal is processed, as well as controls for
adjusting the correction.

The Pitch Correction Meter displays how much the incoming signal is being shifted in cents to match
the target note, which is shown beneath the meter. The target note is determined by the set scale.

You can adjust the intensity of the pitch correction using the Correction Strength slider. The higher the
value, the more the audio is shifted to match the target note. Use the Smooth toggle to switch
smoothing on or off. When enabled, pitch transitions between notes are smoothed, and more natural
vibrato is retained. You can set the smoothing time from 0 to 200 milliseconds using the Smoothing
Time slider. The Correction Strength and Smoothing parameters determine the overall style of the pitch
correction. With these settings, you can produce results ranging from subtle and nuanced to rigid and
quantized.

The Included Notes in Scale display determines which notes are used for the pitch correction. You can
create a custom scale by selecting notes in the display, or you can set the key and scale using the
Root and Scale choosers. The Pitch Shift slider can be used to transpose the pitch up or down in scale
degrees; the pitch shift is applied after the correction.

Auto Shift supports scale awareness: when the Use Current Scale toggle in the device title bar is
enabled, the Quantizer follows the clip’s current scale. Additionally, the Included Keys in Scale
display highlights the selected scale’s notes in purple, and the Root and Scale choosers are
deactivated.

26.4.3 MIDI Tab

Auto Shift’s MIDI Tab.

When MIDI input is activated, the Quantizer tab is replaced with the MIDI tab, where you can
customize the behavior of incoming MIDI.

The piano visualization displays notes as they are received from the source track. These notes are then
used to correct the incoming audio.

Using MIDI Notes to Pitch Correct Audio.

Note that scale awareness is not available when using MIDI input. To use the notes within a specific
scale, you can add the Scale MIDI effect to the source track. Make sure Auto Shift’s Tapping Point
chooser is set to Post FX or Post Mixer so that the effect is included.

The Attack Time slider sets the attack time of the note’s envelope from 0 to 1,000 milliseconds. The
Release Time slider sets the release time of the note’s envelope from 0 to 5 seconds.

When the Note Latch toggle is switched on, MIDI notes are held until the next Note On message. The
Pitch Bend Range control sets the device’s pitch bend range, from 0 to 48 semitones.

In the Mod Routing section, four parameters can be modulated using MIDI or MPE data: Pitch,
Formant, Volume, and Pan. Each parameter can be modulated by one of six modulation sources:
Velocity, Pressure, Mod Wheel, Pitch Bend, Note PB, or Slide. Use each target’s dedicated Mod
Source drop-down menu to select a modulation source, and adjust the modulation depth with its
corresponding Mod Depth slider.

26.4.4 LFO Tab

Auto Shift’s LFO Tab.

You can use the built-in LFO to apply modulation to the incoming audio’s pitch, formants, volume, and
panning.

The LFO Reset toggle switches LFO re-triggering on or off. When enabled, the LFO’s phase will be re-
triggered at note onsets. When using the Quantizer, an onset occurs when a pitch is detected after a
period of unpitched audio. The Onset Indicator LED flashes when the LFO’s phase is re-triggered.
With MIDI input, an onset occurs at the start of a new note, and the Onset Indicator becomes the
Trigger Indicator.

The LFO Delay slider sets the delay time before the attack phase begins, from 0 to 1.5 seconds. The
LFO Attack slider sets the attack time during which the LFO’s level increases to its peak level, from 0 to
2 seconds. As you modify either value, the waveform in the display will reflect the changes.

You can select from nine modulation waveforms using the LFO Waveform drop-down menu: Sine,
Triangle, Triangle 8, Triangle 16, Saw Up, Saw Down, Rectangle, Random, and Random S&H.

The LFO Rate slider lets you select the speed of the LFO in milliseconds or tempo-synced beat
divisions, as determined by the LFO Sync toggles.

In the Mod Routing section, you can modulate four parameters using the LFO: Pitch, Formant, Volume,
and Pan. The individual Mod Depth sliders set the amount of modulation that is applied to each
parameter.

Note that the LFO modulation affects the incoming signal regardless of whether it is being pitch-
corrected.

26.4.5 Pitch Section

Auto Shift’s Pitch Section.

You can apply both pitch and formant shifting to incoming signals using the controls in the Pitch
section.

The Pitch Shift control sets the amount of transposition applied in semitones. You can use the Pitch Shift
Fine slider to set the transposition in cents.

Use the Formant Shift control to shift the formants — the resonant frequencies that help define the tonal
characteristics of a sound — within a range of -100% to 100%. At higher values, pitches will sound
higher and more resonant, while at lower values pitches will sound lower and less full. Shifting
formants lets you create a higher or lower sound without actually transposing the pitch.

The Formant Follow slider determines how much of the formant shifting follows the pitch shifting; higher
values result in a more natural-sounding transposition.

Note that you can use the Pitch Shift and Formant Shift controls with or without pitch correcting the
signal.

26.4.6 Vibrato Section

Auto Shift’s Vibrato Section.

The Vibrato section contains controls for applying vibrato to incoming audio and adjusting the overall
balance of the dry and processed signal.

There are three main vibrato controls:

•
•
•

Vibrato Amount — adjusts the depth of the vibrato, from 0 to 200 cents.
Vibrato Rate — adjusts the speed of the vibrato, from 2 to 15 Hz.
Vibrato Fade In — adjusts the vibrato’s fade-in time in milliseconds.

Enabling the Natural Vibrato toggle creates variations in the vibrato’s speed and depth, producing a
more realistic effect.

Note that you can use the vibrato controls with or without pitch correcting the signal.

The Dry/Wet slider sets the balance between the dry and processed signals. At 0%, no pitch
correction is applied, while at 100%, only the pitch corrected signal is heard. You can create a
doubler effect by setting this value to 50%, which equally balances the original and corrected signals.

26.5 Beat Repeat

The Beat Repeat Effect.

Beat Repeat allows for the creation of controlled or randomized repetitions of an incoming signal.

The Interval control defines how often Beat Repeat captures new material and begins repeating it.
Interval is synced to and set in terms of the song tempo, with values ranging from ”1/32” to ”4 Bars.”
The Offset control shifts the point defined by Interval forward in time. If Interval is set to ”1 Bar,” for
example, and Offset to ”8/16”, material will be captured for repetition once per bar on the third beat
(i.e., halfway, or eight-sixteenths of the way, through the bar).

You can add randomness to the process using the Chance control, which defines the likelihood of
repetitions actually taking place when Interval and Offset ”ask” for them. If Chance is set to 100
percent, repetitions will always take place at the given Interval/Offset time; if set to zero, there will be
no repetitions.

Gate defines the total length of all repetitions in sixteenth notes. If Gate is set to ”4/16”, the
repetitions will occur over the period of one beat, starting at the position defined by Interval and
Offset.

Activating the Repeat button bypasses all of the above controls, immediately capturing material and
repeating it until deactivated.

The Grid control defines the grid size — the size of each repeated slice. If set to ”1/16”, a slice the
size of one sixteenth note will be captured and repeated for the given Gate length (or until Repeat is
deactivated). Large grid values create rhythmic loops, while small values create sonic artifacts. The
No Triplets button sets grid division as binary.

Grid size can be changed randomly using the Variation control. If Variation is set to ”0”, grid size is
fixed. But when Variation is set to higher values, the grid fluctuates considerably around the set Grid
value. Variation has several different modes, available in the chooser below: Trigger creates
variations of the grid when repetitions are triggered; 1/4, 1/8 and 1/16 trigger variations in regular
intervals; and Auto forces Beat Repeat to apply a new random variation after each repetition — the
most complex form of grid variation in Beat Repeat (especially if triplets are also allowed).

Beat Repeat’s repetitions can be pitched down for special sonic effects. Pitch is adjusted through
resampling in Beat Repeat, lengthening segments to pitch them down without again compressing them
to adjust for the length change. This means that the rhythmical structure can become quite ambiguous
with higher Pitch values. The Pitch Decay control tapers the pitch curve, making each repeated slice
play lower than the previous one. Warning: This is the most obscure parameter of Beat Repeat.

Beat Repeat includes a combined low-pass and high-pass filter for defining the passed frequency
range of the device. You can turn the filter on and off, and set the center frequency and width of the
passed frequency band, using the respective controls.

The original signal (which was received at Beat Repeat’s input) is mixed with Beat Repeat’s repetitions
according to one of three mix modes: Mix allows the original signal to pass through the device and
have repetitions added to it; Insert mutes the original signal when repetitions are playing but passes it
otherwise; and Gate passes only the repetitions, never passing the original signal. Gate mode is
especially useful when the effect is housed in a return track.

You can set the output level of the device using the Volume control, and apply Decay to create
gradually fading repetitions.

26.6 Cabinet

The Cabinet Effect.

Cabinet is an effect that emulates the sound of five classic guitar cabinets. Developed in collaboration
with Softube, Cabinet uses physical modelling technology to provide a range of authentic sounds,
with optimized mics and mic positioning.

The Speaker chooser allows you to select from a variety of speaker sizes and combinations. The
chooser’s entries indicate the number of speakers and the speaker size in inches. For example, ”4x12”
means four 12-inch speakers. In the real world, more and larger speakers generally means higher
volumes.

The Microphone chooser changes the position of the virtual microphone in relation to the speaker
cabinet. Near On-Axis micing results in a bright, focused sound, while Near Off-Axis is more resonant
and a bit less bright. Choose the Far position for a balanced sound that also has some characteristics
of the virtual ”room.”

Cabinet Mic Positions.

The switch below the Microphone chooser toggles between a Dynamic and Condenser mic. Dynamic
mics are a bit grittier and commonly used when close-micing guitar cabinets because they are
capable of handling much higher volumes. Condenser mics are more accurate, and are commonly
used for micing from a distance. Of course, Cabinet’s virtual condenser mic won’t be damaged by
high volume levels, so feel free to experiment.

The Output switch toggles between mono and stereo (Dual) processing. Note that in Dual mode,
Cabinet uses twice as much CPU.

The Dry/Wet control adjusts the balance between the processed and dry signals.

26.6.1 Cabinet Tips

Here are some tips for using Cabinet:

26.6.1.1 Amps and Cabinets

Guitar cabinets are normally fed by guitar amps. For this reason, Cabinet is paired with Amp, and the
two are normally used together. But you can also achieve interesting and exotic sounds by using Amp
and Cabinet separately.

26.6.1.2 Multiple mics

A common studio technique is to use multiple mics on a single cabinet, and then adjust the balance
during mixing. This is easy to do by using Live’s Audio Effect Racks. Try this:

1.
2.
3.
4.
5.

Configure one instance of Cabinet as you like.
Put the Cabinet into an Audio Effect Rack.
Duplicate the Rack chain that contains the original Cabinet as many times as you like.
In the additional chains, choose a different Microphone setting and/or mic type.
Adjust the relative volumes of the Rack’s chains in the Rack’s mixer.

26.7 Channel EQ

The Channel EQ Effect.

Inspired by EQs found on classic mixing desks, Channel EQ is a simple, yet flexible three-band EQ,
fine-tuned to provide musical results for a variety of audio material.

Activating the HP 80 Hz switch will toggle a high-pass filter, which is useful for removing the rumble
from a signal.

The Low parameter controls the gain of a low shelf filter, tuned to 100 Hz. This filter can boost or
attenuate low frequencies by a range of +/- 15 dB. The filter curve is adaptive and will change
dynamically relative to the amount of gain applied.

The Mid parameter controls the gain of a sweepable peak filter. Unlike the Low and High parameters,
Mid has a range of +/- 12 dB. The frequency slider located above the Mid control allows you to set
the center frequency of this filter from 120 Hz to 7.5 kHz.

When boosting, the High parameter controls the gain of a high shelf filter, up to 15 dB. When
attenuating, the shelving filter is combined with a low-pass filter. Turning the parameter from 0 dB
towards -15 dB will simultaneously reduce the cutoff frequency of the low-pass filter from 20 kHz to 8
kHz.

A spectrum visualization provides real-time visual feedback of the resulting filter curves and processed
signal.

The Output control sets the amount of gain applied to the processed signal, and can be used to
compensate for any changed signal amplitude resulting from the EQ settings.

26.7.1 Channel EQ Tips

You can use Channel EQ to further shape the output of a reverb effect in a device chain.

You can also shape the sound of a single drum or an entire drum kit, by placing an instance of
Channel EQ onto one or multiple Drum Rack pads.

Adding an instance of Saturator after Channel EQ in a device chain allows you to simulate the
analog nonlinearities of a mixer channel strip. In such cases, boosting the low end considerably
would also lead to increased distortion, similar to the behavior of analog mixing desks.

26.8 Chorus-Ensemble

The Chorus-Ensemble Effect.

Chorus-Ensemble offers a classic two-delay line chorus with an optional third delay line mode. With a
wide variety of tools for thickening sounds, creating flanging and vibrato effects, this device also
allows you to easily recreate string ensemble chorus sounds.

Three different modes are provided, which can be chosen in the display: Classic, Ensemble, and
Vibrato.

Classic mode creates a thickened sound by adding two time-modulated delayed signals to the input.
Use it for a classic chorus sound, adding light motion to your audio signal.

Ensemble mode is inspired by a thick three-delay line chorus pedal used in the ’70s. Ensemble mode
is based on and shares controls with Classic mode, but creates richer, smoother, and more intense
chorus sound by using three delayed signals with evenly split modulation phase offsets.

Vibrato mode applies stronger modulation than a chorus to create pitch variation. The shape of the
modulation waveform can morph seamlessly from a sine to a triangle, and be used to create well-
known “police siren” sounds.

In addition to the mode selector buttons, the display also provides access to a high-pass filter and the
Width parameter. Width is active in Classic and Ensemble modes, but while in Vibrato mode, this
parameter is replaced by Offset and Shape controls.

When enabled, the high-pass filter reduces the chorus effect on signal components below the
frequency set by the High-Pass Frequency slider, ranging from 20 Hz to 2000 Hz.

Width sets the stereo width of the wet signal, which in turn adjusts the chorus level balance between
the mid and side channels. At 0% the signal will be mono, at 100% the balance is equal, and at
200% the chorus level is twice as loud in the sides as in the middle. This is used for maintaining the
level of the effect across the stereo field, which can be helpful during mixing.

When using Vibrato mode, Offset adjusts the amount of phase offset between the waveforms for the
left and right channel. At 180°, the channels will be perfectly out of phase. Shape enables you to
change the shape of the modulation waveform between a sine and a triangle.

Global parameters available include Rate, Amount, Feedback, Output, Warmth and Dry/Wet.

Rate sets the modulation rate in Hertz, and can be adjusted either with the dial or by dragging up or
down in the display. Turn up Rate for a more drastic chorus sound, or keep it low for more gentle
phasing.

Amount adjusts the amplitude of the modulation signals that affects delay times. Higher values result in
a stronger time deviation from the unmodulated time setting.

Feedback sets the amount of each channel’s output that is fed back to its input. Increasing this sounds
more extreme and tends to increase upper harmonic material, and will also create audible delays if
playback is stopped. The feedback signal can be inverted using the Ø button, which results in a
“hollow” sound when combined with high feedback values.

Output sets the amount of gain applied to the processed signal.

Warmth adds slight distortion and filtering for a warmer sound. Turn it up for more crunch!

Dry/Wet adjusts the balance between the processed and dry signals. Set it to 100% when using
Chorus-Ensemble in a return track. Note that this is disabled in Vibrato mode.

26.8.1 Chorus-Ensemble Tips

Here are some tips for using Chorus-Ensemble:

•

•

Use Ensemble mode at a rate between 1 Hz and 1.8 Hz and 100% Amount on dry guitars to
create a typical surf-rock sound.
Automate the Feedback Invert toggle at Feedback levels > 90% to create massive bursts of
decaying oscillations.

26.9 Compressor

The Compressor Effect.

A compressor reduces gain for signals above a user-settable threshold. Compression reduces the
levels of peaks, opening up more headroom and allowing the overall signal level to be turned up. This
gives the signal a higher average level, resulting in a sound that is subjectively louder and ”punchier”
than an uncompressed signal.

A compressor’s two most important parameters are the Threshold and the compression Ratio.

The Threshold slider sets where compression begins. Signals above the threshold are attenuated by an
amount specified by the Ratio parameter, which sets the ratio between the input and output signal. For
example, with a compression ratio of 3, if a signal above the threshold increases by 3 dB, the
compressor output will increase by only 1 dB. If a signal above the threshold increases by 6 dB, then
the output will increase by only 2 dB. A ratio of 1 means no compression, regardless of the threshold.

The orange Gain Reduction meter shows how much the gain is being reduced at any given moment.
The more reduction, the more audible the effect; a gain reduction above 6 dB or so might produce the
desired loudness, but significantly alters the sound and is easily capable of destroying its dynamic
structure. This is something that cannot be undone in later production steps. Keep this in mind
especially when using a compressor, limiter, or sound loudness-maximizing tool in the Main track.
Less is often more here.

Because compression reduces the volume of loud signals and opens up headroom, you can use the
Output (Out) control so that the peaks once again hit the maximum available headroom. The Output
meter shows the output signal’s level. Enabling the Makeup button automatically compensates the
output level if the threshold and ratio settings change.

Dry/Wet adjusts the balance between the compressed and uncompressed signals. At 100%, only the
compressed signal is heard, while at 0%, the device is effectively bypassed.

The Knee control adjusts how gradually or abruptly compression occurs as the threshold is
approached. With a setting of 0 dB, no compression is applied to signals below the threshold, and full
compression is applied to any signal at or above the threshold. With very high ratios, this so-called
”hard knee” behavior can sound harsh. With higher (or ”soft”) knee values, the compressor begins
compressing gradually as the threshold is approached. For example, with a 10 dB knee and a -20 dB
threshold, subtle compression will begin at -30 dB and increase so that signals at -10 dB will be fully
compressed.

Compressor’s display can be switched between several modes via switches in the bottom corners of
the display:

•

The Collapsed view shows only the essential controls.

Compressor’s Collapsed View.

•

The Transfer Curve shows the input level on the horizontal axis and output level vertically. This
view is useful for setting the Knee parameter, which is visible as a pair of dotted lines around
the threshold.

Compressor’s Transfer Curve.

•

The Activity view shows the level of the input signal in light gray. In this mode, the GR and
Output switches toggle between showing the amount of gain reduction in orange or the output
level in a darker gray. These views are useful for visualizing what’s happening to the signal over
time.

Compression Activity Display, Showing Input and Output.

The Attack and Release controls are essential parameters for controlling the response time of
Compressor by defining how fast it reacts to input-level changes.

Attack defines how long it takes to reach maximum compression once a signal exceeds the threshold,
while Release sets how long it takes for the compressor to return to normal operation after the signal
falls below the threshold. With Auto Release enabled, the release time will adjust automatically based
on the incoming audio.

A slight amount of attack time (10-50 ms) allows peaks to come through unprocessed, which helps
preserve dynamics by accentuating the initial portion of the signal. If these peaks cause overloads,
you can try shortening the attack time, but extremely short times take the ”life” out of the signal, and
may lead to a slight “buzziness” caused by distortion. Short release times can cause ”pumping” as
the compressor tries to figure out whether to compress or not; while generally considered an
undesirable effect, some engineers use it on full drum kits to give unusual ”sucking” effects. Careful
adjustment of attack and release times is essential when it comes to compression of rhythmical
sources. If you are not used to working with compressors, play a drum loop and spend some time
adjusting Attack, Release, Threshold and Gain. It can be very exciting!

A compressor can only react to an input signal once it occurs. Since it also needs to apply an attack/
release envelope, the compression is always a bit too late. A digital compressor can solve this
problem by simply delaying the input signal a little bit. Compressor offers three different Lookahead
times: zero ms, one ms and ten ms. The results may sound pretty different depending on this setting.

Compressor can be switched between three basic modes of operation. With Peak selected,
Compressor reacts to short peaks within a signal. This mode is more aggressive and precise, and so
works well for limiting tasks where you need to ensure that there are absolutely no signals over the set
threshold. RMS mode causes Compressor to be less sensitive to very short peaks and compress only
when the incoming level has exceeded the threshold for a slightly longer time. RMS is closer to how
people actually perceive loudness and is usually considered more musical. Expand mode lets you set
the ratio of expansion between the input and output level. For example, a ratio of 1 to 2 means that
for every 1 dB of input above the threshold level, the output level will increase by 2 dB. A ratio of 1 to
1 results in no expansion. For more information about the various types of dynamics processing, see
the Multiband Dynamics section.

In addition to these modes, Compressor can be switched between two envelope follower shapes that
offer further options for how the device measures and responds to signal levels. In linear (Lin) mode,
the speed of the compression response is determined entirely by the Attack and Release values. In
logarithmic (Log) mode, sharply compressed peaks will have a faster release time than less
compressed material. This can result in smoother and less noticeable compression than Lin mode.
Note that the Lin/Log switch is not visible in Compressor’s collapsed view.

26.9.1 Sidechain Parameters

The Compressor Device With Sidechain Section.

Normally, the signal being compressed and the input source that triggers the compressor are the same
signal. But by using sidechaining, it is possible to compress a signal based on the level of another
signal or a specific frequency component. To access the Sidechain parameters, unfold the
Compressor window by toggling the

 button in its title bar.

The sidechain parameters are divided into two sections. On the left are the external controls. Enabling
this section with the Sidechain button allows you to select any of Live’s internal routing points from the
choosers below. This causes the selected source to act as the compressor’s trigger, instead of the
signal that is actually being compressed.

The Gain knob adjusts the level of the external sidechain’s input, while the Dry/Wet knob allows you
to use a combination of sidechain and original signal as the compressor’s trigger. With Dry/Wet at
100%, the compressor is triggered entirely by the sidechain source. At 0%, the sidechain is effectively
bypassed. Note that increasing the gain does not increase the volume of the source signal in the mix.
The sidechain audio is only a trigger for the compressor and is never actually heard.

Note that automatic Makeup is not available when using external sidechain.

On the right of the external section are the controls for the sidechain EQ. Enabling this section causes
the compressor to be triggered by a specific band of frequencies, instead of a complete signal. These
can either be frequencies in the compressed signal or, by using the EQ in conjunction with an external
sidechain, frequencies in another track’s audio.

The headphones button between the external and EQ sections allows you to listen to only the
sidechain input, bypassing the compressor’s output. Since the sidechain audio isn’t fed to the output,
and is only a trigger for the compressor, this temporary listening option can make it much easier to set
sidechain parameters and hear what’s actually making the compressor work.

26.9.2 Compressor Tips

This section presents some tips for using Compressor effectively, particularly with the sidechain
options.

26.9.2.1 Mixing a Voiceover

Sidechaining is commonly used for so-called ”ducking” effects. For example, imagine that you have
one track containing a voiceover and another track containing background music. Since you want the
voiceover to always be the loudest source in the mix, the background music must get out of the way
every time the narrator is speaking. To do this automatically, insert a Compressor on the music track,
but select the narration track’s output as the external sidechain source.

26.9.2.2 Sidechaining in Dance Music

Sidechaining/ducking is a dance music producer’s secret weapon because it can help to ensure that
basslines (or even whole mixes) always make room for the kick drum. By inserting a compressor on

the bass (or Main) track and using the kick drum’s track as the sidechain input, you can help to control
problematic low frequencies that might interfere with the kick drum’s attack.

Using the sidechain EQ in conjunction with this technique can create ducking effects even if you only
have a mixed drum track to work with (as opposed to an isolated kick drum). In this case, insert the
Compressor on the track you want to duck. Then choose the drum track as the external sidechain
source. Then enable the sidechain EQ and select the low-pass filter. By carefully adjusting the
Frequency and Q settings, you should be able to isolate the kick drum from the rest of the drum mix.
Using the sidechain listen mode can help you tune the EQ until you find settings you’re happy with.

Note that Compressor’s internal algorithms were updated in Live 9, in collaboration with Dr. Joshua D.
Reiss of the Centre for Digital Music, Queen Mary University of London.

26.10 Corpus

The Corpus Effect.

Corpus is an effect that simulates the acoustic characteristics of seven types of resonant objects.
Developed in collaboration with Applied Acoustics Systems, Corpus uses physical modeling
technology to provide a wide range of parameters and modulation options.

26.10.1 Resonator Parameters

Corpus’s Resonator Parameters.

The Resonance Type chooser allows you to select from seven types of physically modeled resonant
objects:

•
•

•
•

•

•

•

Beam simulates the resonance properties of beams of different materials and sizes.
Marimba, a specialized variant of the Beam model, reproduces the characteristic tuning of
marimba bar overtones which are produced as a result of the deep arch-cut of the bars.
String simulates the sound produced by strings of different materials and sizes.
Membrane is a model of a rectangular membrane (such as a drum head) with a variable size
and construction.
Plate simulates sound production by a rectangular plate (a flat surface) of different materials
and sizes.
Pipe simulates a cylindrical tube that is fully open at one end and has a variable opening at the
other (adjusted with the Opening parameter).
Tube simulates a cylindrical tube that is fully open at both ends.

The Resonator Quality chooser controls the trade-off between the sound quality of the resonators and
performance by reducing the number of overtones that are calculated. Eco uses minimal CPU
resources, while High creates more sophisticated resonances. This parameter is not used with the Pipe
or Tube resonators.

The Decay slider adjusts the amount of internal damping in the resonator, and thus the decay time.

The Material slider adjusts the variation of the damping at different frequencies. At lower values, low
frequency components decay slower than high frequency components (which simulates objects made
of wood, nylon or rubber). At higher values, high frequency components decay slower (which
simulates objects made of glass or metal). This parameter is not used with the Pipe or Tube resonators.

The Radius slider is only available for the Pipe and Tube resonators, and appears in place of the
Material parameter mentioned above. Radius adjusts the radius of the pipe or tube. As the radius
increases, the decay time and high frequency sustain both increase. At very large sizes, the
fundamental pitch of the resonator also changes.

The Decay and Material/Radius parameters can also be controlled with the X-Y controller.

The Bright knob adjusts the amplitude of various frequency components. At higher values, higher
frequencies are louder. This parameter is not used with the Pipe or Tube resonators.

Inharm (Inharmonics) adjusts the pitch of the resonator’s harmonics. At negative values, frequencies
are compressed, increasing the number of lower partials. At positive values, frequencies are stretched,
increasing the number of upper partials. This parameter is not used with the Pipe or Tube resonators.

Opening, which is only available for the Pipe resonator, scales between an open and closed pipe. At
0%, the pipe is fully closed on one side, while at 100% the pipe is open at both ends.

Ratio, which is only available for the Membrane and Plate resonators, adjusts the ratio of the
membrane/plate along its x and y axes.

The Hit knob adjusts the location on the resonator at which the object is struck or otherwise activated.
At 0%, the object is hit at its center. Higher values move the activation point closer to the edge. This
parameter is not used with the Pipe or Tube resonators.

The Width slider adjusts the stereo mix between the left and right resonators. At 0%, both resonators
are fed equally to each side, resulting in mono output. At 100%, each resonator is sent exclusively to
one channel.

The Pos. L and Pos. R controls adjust the location on the left and right resonator where the vibrations
are measured. At 0%, the resonance is monitored at the object’s center. Higher values move the
listening point closer to the edge. These parameters are not used with the Pipe or Tube resonators,
which are always measured in the middle of their permanently open end.

The Tune knob adjusts the frequency of the resonator in Hertz. When MIDI Frequency is enabled in
Corpus’s Sidechain section, the knob can be used to adjust the coarse tuning of the MIDI modulation.

The Fine knob allows for fine tuning MIDI modulation in cents when sidechain MIDI Frequency is
enabled.

Spread detunes the two resonators in relation to each other. Positive values raise the pitch of the left
resonator while lowering the pitch of the right one, while negative values do the opposite. At 0%, the
resonators are tuned the same.

26.10.2 LFO Section

Corpus’s LFO Section.

Corpus contains a Low Frequency Oscillator (LFO) to modulate the resonant frequency. The Amount
control sets how much the LFO affects the frequency.

The Rate control specifies the LFO speed. It can be set in terms of Hertz, or synced to the song tempo,
allowing for controlled rhythmic modulation.

Available LFO waveform shapes are sine (creates smooth modulations with rounded peaks and
valleys), square, triangle, sawtooth up, sawtooth down and two types of noise (stepped and smooth).

Although only one set of LFO controls is visible, there are actually two LFOs, one for each stereo
channel. The Phase and Spin controls define the relationship between these two LFOs.

Phase keeps both LFOs at the same frequency, but can set the two LFO waveforms ”out of phase” with
each other, creating stereo movement. When set to 180, the LFO outputs are 180 degrees apart, so
that when one LFO reaches its peak, the other is at its minimum. With Phase set to 360 or 0 the two
LFOs run in sync.

When the LFOs are synced to song tempo, an additional Offset knob is available, which shifts the start
point of the LFO along its waveform.

Spin (only available when the LFOs are in Hertz mode) detunes the two LFO speeds relative to each
other. Each stereo channel is modulated at a different frequency, as determined by the Spin amount.

Phase or Spin can be chosen when the LFOs are in Hertz mode using the LFO Stereo mode icons.

The LFO Stereo Mode Icons.

For the noise waveforms, the Phase and Spin controls are not relevant and do not affect the sound.

26.10.3 Filter Section

Corpus’s Filter Section.

The processed signal can be fed through a band-pass filter that can be toggled on or off with the Filter
switch.

The Freq knob adjusts the center frequency of the filter while Bdwidth adjusts the bandwidth of the
filter.

26.10.4 Global Parameters

Corpus’s Global Parameters.

Bleed mixes a portion of the unprocessed signal with the resonated signal. At higher values, more of
the original signal is applied. This is useful for restoring high frequencies, which can often be damped
when the tuning or quality are set to low values. This parameter is deactivated with the Pipe or Tube
resonators.

Gain boosts or attenuates the level of the processed signal. Corpus contains a built-in limiter that
automatically activates when the audio level is too high. This is indicated by the LED next to the Gain
knob.

The Dry/Wet control adjusts the balance between the dry input signal and the signal sent to Corpus’s
processing. Turning Dry/Wet down will not cut resonances that are currently sounding, but rather stop
new input signals from being processed.

26.10.5 Sidechain Parameters

Corpus’s Sidechain Parameters.

The frequency and/or decay rate of the resonance can be MIDI-modulated by enabling the
Frequency and/or Off Decay switches in the Sidechain section. Toggle the
bar to access Sidechain parameters. This button will light up if the sidechain is active.

 button in Corpus’s title

The MIDI From choosers allow you to select the MIDI track and tapping point from which to receive
MIDI note information.

With Frequency enabled, the tuning of the resonance is determined by the incoming MIDI note. If
multiple notes are held simultaneously, the Last/Low switch determines whether the last or the lowest
note will have priority. The Transpose and Fine knobs in the Resonator section allow for coarse and
fine offset of the MIDI-modulated tuning. PB Range sets the range in semitones of pitch bend
modulation.

With Frequency deactivated, the Tune control in the Resonator section adjusts the base frequency of
the resonance in Hertz. The corresponding MIDI note number and fine tuning offset in cents is
displayed below.

Enabling Off Decay causes MIDI Note Off messages to mute the resonance. The slider below the
switch determines the extent to which MIDI Note Off messages mute the resonance. At 0%, Note Offs
are ignored, and the decay time is based only on the value of the Decay parameter, which can be
adjusted using the X-Y controller or Decay slider. This is similar to how real-world mallet instruments
such as marimbas and glockenspiels behave. At 100%, the resonance is muted immediately at Note
Off, regardless of the Decay time.

26.11 Delay

The Delay Effect.

The Delay provides two independent delay lines, one for each channel (left and right).

To refer delay time to the song tempo, activate the Sync switch, which allows using the Delay Time
beat division chooser. The numbered switches represent time delay in 16th notes. For example,
selecting ”4” delays the signal by four 16th notes, which equals one beat (a quarter note) of delay.

If the Sync switch is off, the delay time reverts to milliseconds. In this case, to edit the delay time, click
and drag up the Delay Time knob.

With Stereo Link engaged, the left channel’s settings are applied to the right channel, and changing
either channel’s Sync switch or Delay Time settings will apply the changes to both sides.

The Feedback parameter defines how much of each channel’s output signal feeds back into the delay
lines’ inputs. Internally, they are two independent feedback loops, so a signal on the left channel does
not feed back into the right channel and vice versa.

 button will cause the delay to endlessly cycle the audio which is in its buffer at the moment

The
that the button is pressed, ignoring any new input until Freeze is disabled.

The delay is preceded by a band-pass filter that can be toggled on and off with a switch, and
controlled with an X-Y controller. To define the filter bandwidth, click and drag on the vertical axis. To
set the position of the frequency band, click and drag on the horizontal axis.

Filter frequency and delay time can be modulated by an LFO, making it possible to achieve a range
of sounds from light chorus-like effects through to heavy contorted noise. The Rate slider sets the
frequency of the modulation oscillator in Hertz. The Filter slider adjusts the amount of modulation that
is applied to the filter, and the Time slider adjusts the amount of modulation that is applied to the delay
time.

Changing the delay time while Delay is processing audio can cause abrupt changes in the sound of
the delayed signal. You can choose between three delay transition modes:

•

•

•

Repitch causes a pitch variation when changing the delay time, similar to the behavior of old
tape delay units. Repitch mode is the default option.
Fade creates a crossfade between the old and new delay times. This sounds a bit similar to time
stretching if the delay time is gradually changed.
Jump immediately jumps to the new delay time. Note that this will cause an audible click if the
delay time is changed while delays are sounding.

Tip: Try using the Time slider to explore the effect of time modulation on the different transition modes.

When the Ping Pong switch is activated, the signal jumps from the left to the right output.

The Dry/Wet control adjusts the balance between the processed and dry signals. Set it to 100
percent when using Delay in a return track. The Dry/Wet parameter’s context menu lets you toggle
Equal-Loudness. When enabled, a 50/50 mix will sound equally loud for most signals.

Sets saved in versions of Live older than Live 10.1 that used Simple Delay or Ping Pong Delay devices
will show an Upgrade button in the title bar of each instance of Delay when loading the Set.
Upgrading the device will preserve the previously used device’s free delay time range, and will only
affect the sound of the Set or preset if the free delay time parameter was either mapped to a Macro
Control or to a Max for Live device.

26.11.1 Delay Tips

26.11.1.1 Glitch Effect

Enable the Stereo Link switch and set the delay time to around 400-500ms. Dial the Feedback to
80% or above. Disable the band-pass filter, adjust the Filter slider to 0%, and set the Time slider to
100%. Select the Fade transition mode and make sure Ping Pong is disabled. Set the Dry/Wet control
to 80% or above.

26.11.1.2 Chorus Effect

Disable the Stereo Link switch, set the left channel’s delay time to 12ms, and adjust the right channel’s
delay time to 17ms. Dial the Feedback to 60%. Enable the band-pass filter, set the Filter Frequency to
750 Hz, and adjust the Width slider to 6.5. Set the Rate slider to 5 Hz, bring the Filter slider to 10%,
and dial the Time slider to 12%. Select the Repitch transition mode and enable the Ping Pong switch.

26.12 Drum Buss

The Drum Buss Effect.

Drum Buss is an analog-style drum processor that was designed to add body and character to a
group of drums, while gluing them together in a tight mix.

The Trim slider lets you reduce the input level before any processing is applied to the signal.

The Comp toggle applies a fixed compressor to the input signal before it is processed by the
distortion. The compressor is optimized for balancing out groups of drums, with fast attack, medium
release and moderate ratio settings, as well as ample makeup gain.

There are three types of distortion which can be applied to the input signal. Each distortion type adds
an increasing degree of distortion, while lending its own character to the overall sound:

•
•
•

Soft: waveshaping distortion
Medium: limiting distortion
Hard: clipping distortion with bass boost

For more intensity, it is possible to drive the input prior to distorting it. The Drive control lets you
determine how much drive is applied to the input signal.

Drum Buss combines commonly-used drum processing tools for shaping the mid-high range and filling
out the low end, which we will look at in the following sections.

26.12.0.1 Mid-High Frequency Shaping

The mid-high frequency shaping tools are designed to add clarity and presence to drums such as
snares and hi-hats.

Crunch adjusts the amount of sine-shaped distortion applied to mid-high frequencies.

The Damp control is a low-pass filter, which removes unwanted high frequencies that can occur after
adding distortion.

The Transients knob emphasizes or de-emphasizes the transients of frequencies above 100 Hz.
Positive values add attack and increase sustain, resulting in a full, “punchy” sound. Negative values
also add attack, but decrease sustain. This tightens up the drums, giving them a sharper, more crisp
sound with less room and rattle.

Low-End Enhancement

Drum Buss’s low-end enhancement is made up of two tools: a resonant filter, which dramatically
boosts bass frequencies, as well as a Decay control, which allows you to adjust the decay rate of both
the incoming audio and the signal processed by the resonant filter. These tools help you to fill out the
low-end of your drums.

The Boom knob adjusts the amount of low-end enhancement that the resonant filter produces. The
Bass Meter lets you see the Boom’s effect on the signal, which can be particularly useful if you can’t
hear it.

The Freq knob adjusts the frequency of the low-end enhancer. Force To Note lets you tune the low-end
enhancer by setting its frequency to the value of the nearest MIDI note.

The Decay control adjusts the decay rate of the low frequencies. When the Boom amount is set to 0%,
the decay affects the incoming (post-drive and distortion) signal only. When the “Boom Level” is
adjusted above 0%, the decay affects both the incoming and processed signals.

To solo the result of the low-frequency enhancer, enable Boom Audition via the headphone icon.

26.12.0.2 Output

The Dry/Wet control adjusts the balance between the processed and dry signals.

The Output Gain slider sets the amount of gain applied to the processed signal.

26.13 Dynamic Tube

The Dynamic Tube Effect.

The Dynamic Tube effect infuses sounds with the peculiarities of tube saturation. An integrated
envelope follower generates dynamic tonal variations related to the level of the input signal.

Three tube models, A, B and C, provide a range of distortion characteristics known from real amplifier
tubes. Tube A does not produce distortions if Bias is set low, but will kick in whenever the input signal
exceeds a certain threshold, creating bright harmonics. Tube C is a very poor tube amp that produces
distortions all the time. The qualities of Tube B lie somewhere between these two extremes.

The Tone control sets the spectral distribution of the distortions, directing them into the higher registers,
or through the midrange and deeper.

The Drive control determines how much signal reaches the tube; greater Drive yields a dirtier output.
The intensity of the tube is controlled by the Bias dial, which pushes the signal into the celebrated
realms of nonlinear distortion. With very high amounts of Bias, the signal will really start to break
apart.

The Bias parameter can be positively or negatively modulated by an envelope follower, which is
controlled with the Envelope knob. The more deeply the envelope is applied, the more the Bias point
will be influenced by the level of the input signal. Negative Envelope values create expansion effects
by reducing distortion on loud signals, while positive values will make loud sounds dirtier.

Attack and Release are envelope characteristics that define how quickly the envelope reacts to
volume changes in the input signal. Together, they shape the dynamic nature of the distortions. Note
that if Envelope is set to zero, they will have no effect.

Cut or boost the device’s final signal level with the Output dial.

Aliasing can be reduced by enabling Hi-Quality mode, which can be accessed via the device title
bar’s context menu. This improves the sound quality, particularly with high frequency signals, but there
is a slight increase in CPU usage.

26.14 Echo

The Echo Effect.

Echo is a modulation delay effect that lets you set the delay time on two independent delay lines,
while giving you control over envelope and filter modulation.

The Channel Mode buttons let you choose between three different modes: Stereo, Ping Pong and
Mid/Side.

The Left and Right delay line controls let you choose the delay time, which can be set in beat divisions
or milliseconds, depending on the state of the Sync switch. Note that when the Mid/Side channel
mode is selected, the Left and Right delay line controls are replaced with Mid and Side knobs.

You can use the Sync Mode choosers to select one of the following beat-synced modes: Notes,
Triplet, Dotted and 16th. Note that when switching between Sync Modes, the resulting changes are
only audible while the Sync switch is set to Sync.

When Stereo Link is engaged, changing either channel’s delay line control, Sync switch or Sync
Mode settings will apply the changes to both sides.

Changing the Delay Offset sliders shortens or extends the delay time by fractional amounts, thus
producing the ”swing” type of timing effect found in drum machines. Note that when Stereo Link is
enabled, the Delay Offset can still be adjusted individually for the two delay lines.

The Input knob sets the amount of gain applied to the dry signal. To apply distortion to the dry signal,
press the “D” button.

The Feedback parameter defines how much of each channel’s output signal feeds back into the delay
lines’ inputs. The “Ø“ button inverts each channel’s output signal before adding it back to their inputs.

26.14.1 Echo Tab

The Echo tab provides a visualization and control of the delay lines and filter parameters.

Echo’s Tunnel Visualization.

The Echo Tunnel’s circular lines represent the individual repeats, progressing from the outside of the
tunnel to its center. The distance between the lines indicates the time between the repeats, and the
white dots in the middle form a fixed 1/8th note grid for reference. You can adjust the delay times for
each delay line by clicking and dragging in the display.

Echo’s Filter.

The Filter toggle enables a high-pass and low-pass filter. The HP slider adjusts the cutoff frequency of
the high-pass filter and the adjacent Res slider adjusts the high-pass filter’s resonance. The LP slider
adjusts the cutoff frequency of the low-pass filter, and you can use the Res slider on the right side to
adjust the low-pass filter’s resonance.

The Filter Display makes it possible to visualize the filter curves. To show or hide the Filter Display, use
the triangular toggle button. You can also adjust the filter parameters by clicking and dragging either
of the filter dots in the Filter Display.

26.14.2 Modulation Tab

Echo’s Modulation tab contains an LFO that modulates filter frequency and delay time, and an
envelope follower that can be blended with the LFO.

Echo’s Modulation Tab.

You can choose from one of six different modulation waveforms including sine, triangle, sawtooth up,
sawtooth down, square, and noise. The selected waveform will appear in the display, which you can
drag to adjust the modulation frequency.

When Sync is enabled, modulation is synchronized to the song tempo. You can use the Rate slider to
set the frequency of the modulation oscillator in beat divisions. When Sync is disabled, you can use
the Freq slider to adjust frequency of the modulation oscillator in Hertz.

Phase adjusts the amount of offset between the waveforms for the left and right channel. At 180°, the
channels will be perfectly out of phase.

Mod Delay adjusts the amount of modulation that is applied to the delay time. Modulation x4 scales
the delay time modulation depth by a factor of four. With short delay times, this produces deep
flanging sounds.

Mod Filter adjusts the amount of modulation that is applied to the filter.

Env Mix blends between the modulation oscillator and an envelope follower. At 100%, only the
envelope’s modulation will be heard. At 0%, only the LFO’s modulation will be heard.

26.14.3 Character Tab

Echo’s Character tab contains parameters that control dynamics and add imperfections to your sound.

Echo’s Character Tab.

Gate enables a gate at Echo’s input. It mutes the signal components below its threshold. Threshold sets
the threshold level that incoming audio signals must exceed in order to open the gate. Release sets
how long it takes for the gate to close after the signal has dropped below the threshold.

When Ducking is enabled, the wet signal is proportionally reduced as long as there is an input signal.
Ducking begins to affect the output signal when the input level exceeds the set Threshold. Release sets
how long it takes for ducking to stop after the input signal drops below the threshold.

When enabled, Noise introduces noise to simulate the character of vintage equipment. You can adjust
the Amount of noise added to the signal, and Morph between different types of noise.

When enabled, Wobble adds an irregular modulation of the delay time to simulate tape delays. You
can adjust the Amount of wobble added to the signal, and Morph between different types of wobble
modulation.

Repitch causes a pitch variation when changing the delay time, similar to the behavior of hardware
delay units. When Repitch is disabled, changing the delay time creates a crossfade between the old
and new delay times.

Note that in order to save CPU, the Echo device turns itself off at least eight seconds after its input
stops producing sound. However, Echo will not switch off if both the Noise and Gate parameters are
enabled.

26.14.4 Global Controls

The Reverb knob sets the amount of reverb added, and you use the Reverb Location chooser to set
where the reverb is added in the processing chain: pre delay, post delay, or within the feedback loop.
Use the Decay slider to lengthen or shorten the reverb tail.

The Stereo control sets the stereo width of the wet signal. 0% yields a mono signal whereas values
above 100% create a widened stereo panorama.

The Output sets the amount of gain applied to the processed signal. The Dry/Wet control adjusts the
balance between the processed and dry signals. Set it to 100 percent when using Echo in a return
track. The Dry/Wet parameter’s context menu lets you toggle Equal-Loudness. When enabled, a
50/50 mix will sound equally loud for most signals.

26.15 EQ Eight

The EQ Eight Effect.

The EQ Eight effect is an equalizer featuring up to eight parametric filters per input channel, useful for
changing a sound’s timbre.

The input signal can be processed using one of three modes: Stereo, L/R and M/S. Stereo mode uses
a single curve to filter both channels of a stereo input equally. L/R mode provides an independently
adjustable filter curve for the left and right channels of a stereo input; M/S mode (Mid/Side)
provides the same functionality for signals that have been recorded using M/S encoding. In all
modes, the frequency spectrum of the output is displayed behind the filter curves when the Analyze
switch is on.

When using the L/R and M/S modes, both curves are displayed simultaneously for reference,
although only the active channel is editable. The Edit switch indicates the active channel, and is used
to toggle between the two curves.

Each filter has a chooser that allows you to switch between eight responses. From top to bottom in the
choosers, these are:

•
•
•
•
•
•

48 or 12 dB/octave Low cut (cuts frequencies below the specified frequency);
Low shelf (boosts or cuts frequencies lower than the specified frequency);
Peak (boosts or cuts over a range of frequencies);
Notch (sharply cuts frequencies within a narrow range);
High shelf (boosts or cuts frequencies higher than the specified frequency);
12 or 48 dB/octave High cut (cuts frequencies above the specified frequency).

Each filter band can be turned on or off independently with an activator switch below the chooser.
Turn off bands that are not in use to save CPU power. To achieve really drastic filtering effects, assign
the same parameters to two or more filters.

To edit the filter curve, click and drag on the filter dots in the display. Drag-enclose multiple filter dots
to adjust them simultaneously, either with the mouse or with your computer keyboard’s arrow keys.
Horizontal movement changes the filter frequency, while vertical movement adjusts the filter band’s
gain. To adjust the filter Q (also called resonance or bandwidth), hold down the Alt (Win) /
Option (Mac) modifier while dragging the mouse. Note that the gain cannot be adjusted for the low
cut, notch and high cut filters. In these modes, vertical dragging adjusts the filter Q.

To get an even better view, you can toggle the location of the display between the device chain and
Live’s main window by clicking the
 button in EQ Eight’s title bar. When using this expanded view,
all eight filters can be edited simultaneously in the Device View.

EQ Eight’s Controls With the Display Expanded.

By default, EQ Eight’s output spectrum is shown in the display. If you would prefer to work entirely “by
ear,” you can turn off the Analyze button to disable the spectrum view.

With Adaptive Q enabled, the Q amount increases as the amount of boost or cut increases. This
results in a more consistent output volume and is based on the behavior of classic analog EQs.

To temporarily solo a single filter, enable Audition mode via the headphone icon. In Audition mode,
clicking and holding on a filter dot allows you to hear only that filter’s effect on the output.

You can also select a band for editing by clicking near its number and then edit parameter values with
the Freq, Gain and Q dials (and/or type values into the number fields below each dial).

As boosting will increase levels and cutting will decrease levels, use the global Gain slider to optimize
the output level for maximum level consistent with minimum distortion.

The Scale field will adjust the gain of all filters that support gain (all except low cut, notch and high
cut).

26.15.0.1 Context Menu Options for EQ Eight

Several of EQ Eight’s controls are only available via the device title bar’s context menu. These include:

•

Oversampling - enabling this option causes EQ Eight to internally process two times the current
sample rate, which allows for smoother filter behavior when adjusting high frequencies. There is
a slight increase in CPU usage with Oversampling enabled.

26.16 EQ Three

The EQ Three Effect.

If you have ever used a good DJ mixer you will know what this is: An EQ that allows you to adjust the
level of low, mid and high frequencies independently.

Each band can be adjusted from -infinite dB to +6 dB using the gain controls. This means that you can
completely remove, for example, the bass drum or bassline of a track, while leaving the other
frequencies untouched.

You can also turn on or off each band using the On/Off buttons located under the gain controls.
These buttons are especially handy if assigned to computer keys.

EQ Three gives you visual confirmation of the presence of a signal in each frequency band using three
LEDs. Even if a band is turned off, you can tell if there is something going on in it. The internal threshold
for the LEDs is set to -24 dB.

The frequency range of each band is defined via two crossover controls: FreqLo and FreqHi. If FreqLo
is set to 500 Hz and FreqHi to 2000 Hz, then the low band goes from 0 Hz to 500 Hz, the mid band
from 500 Hz to 2000 Hz and the high band from 2000 Hz up to whatever your soundcard or
sample rate supports.

A very important control is the 24 dB/48 dB switch. It defines how sharp the filters are cutting the
signal at the crossover frequency. The higher setting results in more drastic filtering, but needs more
CPU.

Note: The filters in this device are optimized to sound more like a good, powerful analog filter
cascade than a clean digital filter. The 48 dB Mode especially does not provide a perfect linear
transfer quality, resulting in a slight coloration of the input signal even if all controls are set to 0.00 dB.
This is typical behavior for this kind of filter, and is part of EQ Three’s unique sound. If you need a
more linear behavior choose 24 dB Mode or use the EQ Eight.

26.17 Erosion

The Erosion Effect.

The Erosion effect degrades the input signal by modulating a short delay with filtered noise or a sine
wave. This adds noisy artifacts or aliasing/downsampling-like distortions that sound very ”digital.”

To change the sine wave frequency or noise band center frequency, click and drag along the X-axis in
the X-Y field. The Y-axis controls the modulation amount. If you hold down the Alt (Win) / Option
(Mac) modifier key while clicking in the X-Y field, the Y-axis controls the bandwidth. Note that
bandwidth is not adjustable when Sine is selected.

The Frequency control determines the color, or quality, of the distortion. If the Mode control is set to
Noise, this works in conjunction with the Width control, which defines the noise bandwidth. Lower
values lead to more selective distortion frequencies, while higher values affect the entire input signal.
Width has no effect in Sine Mode.

Noise and Sine use a single modulation generator. However, Wide Noise has independent noise
generators for the left and right channels, which creates a subtle stereo enhancement.

26.18 External Audio Effect

The External Audio Effect.

The External Audio Effect is a bit different than Live’s other effects devices. Instead of processing audio
itself, it allows you to use external (hardware) effects processors within a track’s device chain.

The Audio To chooser selects the outputs on your computer’s audio hardware that will go to your
external device, while the Audio From chooser selects the inputs that will bring the processed signal
back into Live. As with the track inputs and outputs, the list of available inputs and outputs depends on
the Audio Settings, which can be reached via the ”Configure…” option at the bottom of each chooser.

Below each chooser is a Peak level indicator that shows the highest audio level attained. Click on the
indicators to reset them.

The Gain knobs next to the choosers adjust the levels going out of and back into Live. These levels
should be set carefully to avoid clipping, both in your external hardware and when returning the
audio to your computer.

The Dry/Wet control adjusts the balance between the processed and dry signals. Set it to 100
percent if using the External Audio Effect in a return track.

The Invert button inverts the phase of the processed signal coming back into Live.

Since hardware effects introduce latency that Live cannot automatically detect, you can manually
compensate for any delays by adjusting the Hardware Latency slider. The button next to this slider
allows you to set your latency compensation amount in either milliseconds or samples. If your external
device connects to Live via a digital connection, you will want to adjust your latency settings in

samples, which ensures that the number of samples you specify will be retained even when changing
the sample rate. If your external device connects to Live via an analog connection, you will want to
adjust your latency settings in milliseconds, which ensures that the amount of time you specify will be
retained when changing the sample rate. Note that adjusting in samples gives you finer control, so
even in cases when you’re working with analog devices, you may want to ”fine tune” your latency in
samples in order to achieve the lowest possible latency. In this case, be sure to switch back to
milliseconds before changing your sample rate.

Note: If the Delay Compensation option is unchecked in the Options menu, the Hardware Latency
slider is disabled.

For instructions on how to accurately set up latency compensation for your hardware, please see the
Driver Error Compensation lesson in Live’s Help View.

26.19 Filter Delay

The Filter Delay Effect.

The Filter Delay provides three independent delay lines, each preceded by linked low-pass and high-
pass filters. This allows applying delay to only certain input signal frequencies, as determined by the
filter settings. The feedback from each of the three delays is also routed back through the filters.

Each of the three delays can be switched on and off independently. The Filter Delay device assigns
delay 1 to the input signal’s left channel, delay 2 to the left and right channels and delay 3 to the right
channel. The Pan controls at the right can override the delay channels’ outputs; otherwise each delay
outputs on the channel from which it derives its input.

Each delay channel’s filter has an associated On switch, located to the left of each X-Y controller. The
X-Y controllers adjust the low-pass and high-pass filters simultaneously for each delay. To edit filter
bandwidth, click and drag on the vertical axis; click and drag on the horizontal axis to set the filter
band’s frequency.

To refer delay time to the song tempo, activate the Sync switch, which allows using the Delay Time
beat division chooser. The numbered switches represent time delay in 16th notes. For example,
selecting ”4” delays the signal by four 16th notes, which equals one beat (a quarter note) of delay.
With Sync Mode active, changing the Delay Time field percentage value shortens and extends delay
times by fractional amounts, thus producing the ”swing” type of timing effect found in drum machines.

If the Sync switch is off, the delay time reverts to milliseconds. In this case, to edit the delay time, click
and drag up or down in the Delay Time field, or click in the field and type in a value.

The Feedback parameter sets how much of the output signal returns to the delay line input. Very high
values can lead to runaway feedback and produce a loud oscillation — watch your ears and
speakers if you decide to check out extreme feedback settings!

Each delay channel has its own volume control, which can be turned up to +6 dB to compensate for
drastic filtering at the input.

The Dry control adjusts the unprocessed signal level. Set it to minimum if using Delay in a return track.

26.20 Gate

The Gate Effect.

The Gate effect passes only signals whose level exceeds a user-specified threshold. A gate can
eliminate low-level noise that occurs between sounds (e.g., hiss or hum), or shape a sound by turning
up the threshold so that it cuts off reverb or delay tails or truncates an instrument’s natural decay.

Gate’s display area shows the level of the input signal in light gray and the level of the output signal in
a darker gray with a white outline. This allows you to see the amount of gating that is occurring at any
moment, and helps you to set the appropriate parameters.

The Threshold knob sets the gate’s sensitivity. The Threshold value is represented in the display as a
horizontal blue line, which can also be dragged.

Return (also known as “hysteresis”) sets the difference between the level that opens the gate and the
level that closes it. Higher hysteresis values reduce “chatter” caused by the gate rapidly opening and
closing when the input signal is near the threshold level. The Return value is represented in the display
as an additional horizontal orange line.

With the Flip button enabled, the gate works in reverse; the signal will only pass if its level is below the
threshold.

A gate can only react to an input signal once it occurs. Since it also needs to apply an attack/release
envelope, the gating is always a bit too late. A digital gate can solve this problem by simply delaying
the input signal a little bit. Gate offers three different Lookahead times: zero ms, one ms and ten ms.
The results may sound pretty different depending on this setting.

The Attack time determines how long it takes for the gate to switch from closed to open when a signal
goes from below to above the threshold. Very short attack times can produce sharp clicking sounds,
while long times soften the sound’s attack.

When the signal goes from above to below the threshold, the Hold time kicks in. After the hold time
expires, the gate closes over a period of time set by the Release parameter.

The Floor knob sets the amount of attenuation that will be applied when the gate is closed. If set to -inf
dB, a closed gate will mute the input signal. A setting of 0.00 dB means that even if the gate is closed,
there is no effect on the signal. Settings in between these two extremes attenuate the input to a greater
or lesser degree when the gate is closed.

Normally, the signal being gated and the input source that triggers the gate are the same signal. But
by using sidechaining, it is possible to gate a signal based on the level of another signal. To access
the Sidechain parameters, unfold the Gate window by toggling the

 button in its title bar.

Gate’s Sidechain Parameters.

Enabling this section with the Sidechain button allows you to select another track from the choosers
below. This causes the selected track’s signal to act as the gate’s trigger, instead of the signal that is
actually being gated.

The Gain knob adjusts the level of the external sidechain’s input, while the Dry/Wet knob allows you
to use a combination of sidechain and original signal as the gate’s trigger. With Dry/Wet at 100%,
the gate is triggered entirely by the sidechain source. At 0%, the sidechain is effectively bypassed.
Note that increasing the gain does not increase the volume of the source signal in the mix. The
sidechain audio is only a trigger for the gate and is never actually heard.

Sidechain gating can be used to superimpose rhythmic patterns from one source onto another. For
example, a held pad sound can be triggered with the rhythm of a drum loop by inserting a Gate on
the pad’s track and choosing the drum loop’s track as the sidechain input.

On the right of the external section are the controls for the sidechain EQ. Enabling this section causes
the gate to be triggered by a specific band of frequencies, instead of a complete signal. These can
either be frequencies in the signal to be gated or, by using the EQ in conjunction with an external
sidechain, frequencies in another track’s audio.

The headphones button between the external and EQ sections allows you to listen to only the
sidechain input, bypassing the gate’s output. Since the sidechain audio isn’t fed to the output, and is
only a trigger for the gate, this temporary listening option can make it much easier to set sidechain
parameters and hear what’s actually making the gate work. When this button is on, the display area
shows the level of the sidechain input signal in green.

26.21 Glue Compressor

The Glue Compressor Effect.

The Glue Compressor is an analog-modeled compressor created in collaboration with Cytomic, and
is based on the classic bus compressor from a famous 80’s mixing console. Like Live’s original
Compressor, the Glue Compressor can be used for basic dynamics control of individual tracks, but is
mainly designed for use on the Main track or a Group Track to “glue” multiple sources together into a
cohesive sounding mix.

The Threshold knob sets where compression begins. Signals above the threshold are attenuated by an
amount specified by the Ratio parameter, which sets the ratio between the input and output signal.
Unlike the Compressor, the Glue Compressor does not have a user-adjustable knee. Instead, the knee
becomes more sharp as the ratio increases.

Attack defines how long it takes to reach maximum compression once a signal exceeds the threshold.
The Attack knob’s values are in milliseconds. Release sets how long it takes for the compressor to
return to normal operation after the signal falls below the threshold. The Release knob’s values are in
seconds. When Release is set to A (Auto), the release time will adjust automatically based on the
incoming audio. The Glue Compressor’s Auto Release actually uses two times - a slow one as a base
compression value, and a fast one to react to transients in the signal. Auto Release may be too slow to
react to sudden changes in level, but generally is a useful way to tame a wide range of material in a
gentle way.

Dry/Wet adjusts the balance between the compressed and uncompressed signals. At 100%, only the
compressed signal is heard, while at 0%, the device is effectively bypassed. Another way of
controlling the amount of compression is with the Range slider, which sets how much compression can

occur. Values between about -60 and -70 dB emulate the original hardware, while values between
-40 and -15 dB can be useful as an alternative to the Dry/Wet control. At 0 dB, no compression
occurs.

Makeup applies gain to the signal, allowing you to compensate for the reduction in level caused by
compression. A Makeup value that roughly corresponds to the position of the needle in the display
should result in a level close to what you had before compressing.

The Soft clip switch toggles a fixed waveshaper, useful for taming very loud transients. When enabled,
the Glue Compressor’s maximum output level is -.5 dB. Note that with Oversampling enabled, very
loud peaks may still exceed 0 dB. The Soft clipper is not a transparent limiter, and will distort your
signal when active. We recommend leaving it disabled unless this particular type of “colored”
distortion is what you’re looking for.

The Glue Compressor’s needle display shows the amount of gain reduction in dB. The Clip LED turns
red if the device’s output level is exceeding 0 dB. If Soft clipping is enabled, this LED turns yellow to
indicate that peaks are being clipped.

26.21.1 Sidechain Parameters

The Glue Compressor With Sidechain Section.

Normally, the signal being compressed and the input source that triggers the compressor are the same
signal. But by using sidechaining, it is possible to compress a signal based on the level of another
signal or a specific frequency component. To access the Sidechain parameters, unfold the Glue
Compressor window by toggling the

 button in its title bar.

The sidechain parameters are divided into two sections. On the left are the external controls. Enabling
this section with the Sidechain button allows you to select any of Live’s internal routing points from the
choosers below. This causes the selected source to act as the Glue Compressor’s trigger, instead of the
signal that is actually being compressed.

The Gain knob adjusts the level of the external sidechain’s input, while the Dry/Wet knob allows you
to use a combination of sidechain and original signal as the Glue Compressor’s trigger. With Dry/
Wet at 100%, the Glue Compressor is triggered entirely by the sidechain source. At 0%, the sidechain

is effectively bypassed. Note that increasing the gain does not increase the volume of the source
signal in the mix. The sidechain audio is only a trigger for the Glue Compressor and is never actually
heard.

On the right of the external section are the controls for the sidechain EQ. Enabling this section causes
the Glue Compressor to be triggered by a specific band of frequencies, instead of a complete signal.
These can either be frequencies in the compressed signal or, by using the EQ in conjunction with an
external sidechain, frequencies in another track’s audio.

The headphones button between the external and EQ sections allows you to listen to only the
sidechain input, bypassing the Glue Compressor’s output. Since the sidechain audio isn’t fed to the
output, and is only a trigger for the Glue Compressor, this temporary listening option can make it
much easier to set sidechain parameters and hear what’s actually making the Glue Compressor work.

26.21.1.1 Context Menu Options for Glue Compressor

Oversampling can be toggled on or off via the device title bar’s context menu. Enabling this option
causes the Glue Compressor to internally process at two times the current sampling rate, which may
reduce aliasing and transient harshness. There is a slight increase in CPU usage with Oversampling
enabled. Note that with Oversampling enabled, the level may exceed 0 dB even with Soft clip
enabled.

26.22 Grain Delay

The Grain Delay Effect.

The Grain Delay effect slices the input signal into tiny particles (called ”grains”) that are then
individually delayed and can also have different pitches compared to the original signal source.
Randomizing pitch and delay time can create complex masses of sound and rhythm that seem to bear

little relationship to the source. This can be very useful in creating new sounds and textures, as well as
getting rid of unwelcome house guests, or terrifying small pets (just kidding!).

You can route each parameter to the X-Y controller’s horizontal or vertical axis. To assign a parameter
to the X-axis, choose it from the parameter row below the controller. To assign a parameter to the Y-
axis, use the parameter row on the left side.

To refer delay time to the song tempo, activate the Sync switch, which allows using the Delay Time
beat division chooser. The numbered switches represent time delay in 16th notes. For example,
selecting ”4” delays the signal by four 16th notes, which equals one beat (a quarter note) of delay.
With Sync Mode active, changing the Delay Time field percentage value shortens and extends delay
times by fractional amounts, thus producing the ”swing” type of timing effect found in drum machines.

If the Sync switch is off, the delay time reverts to milliseconds. In this case, to edit the delay time, click
and drag up or down in the Delay Time field, or click in the field and type in a value.

The Delay Time can also be routed to the horizontal axis of the X-Y controller.

The Spray control adds random delay time changes. Low values smear the signal across time, which
adds ”noisiness” to the sound. High Spray values completely break down the structure of the source
signal, introducing varying degrees of rhythmic chaos. This is the recommended setting for anarchists.

The size and duration of each grain is a function of the Frequency parameter. The sound of Pitch and
Spray depends very much on this parameter.

You can transpose the grain pitch with the Pitch parameter, which acts much like a crude pitch shifter.

The Random Pitch control adds random variations to each grain’s pitch. Low values create a sort of
mutant chorusing effect, while high values can make the original source pitch completely
unintelligible. This parameter can interact with the main Pitch control, thus allowing degrees of stability
and instability in a sound’s pitch structure.

The Feedback parameter sets how much of the output signal returns to the delay line input. Very high
values can lead to runaway feedback and produce a loud oscillation — watch your ears and
speakers if you decide to check out extreme feedback settings!

Grain Delay also has a dry/wet control, which can be routed to the vertical axis of the X-Y controller.

26.23 Hybrid Reverb

The Hybrid Reverb Effect.

Hybrid Reverb combines two different approaches to reverberation in one device, blending
convolution reverb with a number of digital reverb algorithms. Using multiple routing options and
parameters, you can create unique reverb sounds, or use Hybrid Reverb to generate drone-like
soundscapes or completely transform any source material.

In addition to providing a selection of impulse responses, Hybrid Reverb allows you to import any
audio file to use as an impulse response (also known as an IR), greatly increasing your sound design
opportunities. Dedicated controls can be employed to shape any chosen impulse response.

The algorithmic engine contains several reverb modes, each providing a different set of parameters
and sonic properties, ranging from clean and creamy to metallic and gong-like.

The convolution and algorithmic engines can be used independently, or combined together in series
or parallel, with their volume relationship being continuously adjustable. An EQ section further shapes
the reverb’s sound and can be selectively applied to the two reverb engines. An additional control
introduces degradation of the signal, emulating the behavior of older digital reverb units.

26.23.1 Signal Flow

You can imagine signals being processed by Hybrid Reverb as flowing from the left side of the device
towards the right side, passing first through the input section, then into the reverb engines. The
relationship between the two reverb engines is affected by the routing section, after which the signal
passes through the EQ section, and then finally to the output.

The convolution reverb engine’s controls are yellow in color, while the algorithmic engine’s controls
are displayed in blue.

26.23.2 Input Section

Using the Send knob, you can choose the amount of gain applied to the signal that feeds the reverb.
Note that the dry signal is not affected and will still pass through the device.

Predelay controls the delay time before the onset of the first early reflection. This delays the
reverberation relative to the input signal. One’s impression of the size of a real room depends partly
on this delay; typical values for “natural” sounds range from 1ms to 25ms. You can choose either a
time-based or beat-synced predelay time using the Predelay Sync buttons.

Feedback sets the amount of the predelay’s output that is fed back to its input. Note that both time-
based and beat-based predelay times have independent feedback settings.

The main window of Hybrid Reverb has two tabs: Reverb and EQ. The Reverb tab contains all controls
related to both the convolution and algorithmic reverb engines. Starting with the Routing chooser in
the center, you’ll find four options:

•

•

•
•

Serial routes the output of the convolution engine into the algorithmic engine. While the
convolution reverb is always active in this mode, Blend controls the amount of convolution
reverb fed into the algorithmic reverb. A setting of 100/0 produces pure convolution reverb,
while 0/100 generates pure algorithmic reverb which has been fed by the convolution reverb’s
output.
Parallel uses both convolution and algorithmic reverb engines, but separates them from each
other. The Blend knob adjusts the level balance between the two different reverb engines, with
a setting of 100/0 generating pure convolution reverb and 0/100 producing pure algorithmic
reverb.
Algorithm uses only the algorithmic reverb engine.
Convolution uses only the convolution reverb engine.

Hybrid Reverb’s user interface changes dynamically, so that when a reverb engine is not in use, its
controls will appear grayed out.

The Blend knob blends between the output of the convolution and algorithm sections when Routing is
set to Serial or Parallel. Note that when either Algorithm or Convolution is selected in the Routing
chooser, the Blend knob will not have an effect.

26.23.3 Convolution Reverb Engine

Hybrid Reverb’s Convolution Reverb Section.

A convolution reverb uses recordings of actual spaces (called impulse responses) to create its effect.
This allows you to place your sounds in practically any space for which you have a recording. For a
more typical reverb sound, this can include some of the most famous halls and studios throughout the

world. With a more creative approach, you can use recordings of anything, from snare drums to
garbage cans, or even instrumental and vocal recordings!

Impulse responses can be chosen in the Convolution IR menu. The upper drop-down menu chooses
the category of impulse response, while the lower drop-down menu chooses a specific impulse
response from within that category. Backward and forward arrow buttons are provided for easy
browsing through impulse responses. These arrow buttons will automatically switch to the next
category when you reach the end of the current one, so you can continuously move through the
impulse responses using the arrows alone. The chosen impulse response’s waveform is then shown in
the main display, which changes based on the Attack, Decay, and Size settings (described below).

The various impulse response categories are: Early Reflections, Real Places, Chambers and Large
Rooms, Made for Drums, Halls, Plates, Springs, Bigger Spaces, Textures, and User.

To add your own impulse responses to the User category, drag and drop the IR audio file into Hybrid
Reverb’s convolution waveform display. If you add a file from a folder that contains other audio files,
all files will be added as impulse responses. Note: if you remove Hybrid Reverb from a track and add
it again, the previously added User samples will no longer be available in the User category.
However, you can drag and drop the samples into the waveform display again to repopulate the list.

The Attack, Decay, and Size parameters control the impulse response’s amplitude envelope. The
Attack parameter controls the attack time of the envelope, while the Decay parameter controls the
decay time of the envelope. The Size parameter adjusts the relative size of the impulse response.

26.23.4 Algorithmic Reverb Engine

Hybrid Reverb’s Algorithmic Reverb Section.

In comparison to the convolution engine, the algorithmic engine is based purely on digital delay lines,
and no samples are used.

To the right of the Blend knob you will find the controls for the algorithmic reverb engine. Different
parameters will be displayed depending on what you choose in the Algorithm chooser.

Five different algorithms are available: Dark Hall, Quartz, Shimmer, Tides and Prism. For all
algorithms, the Decay, Size, Delay and Freeze parameters are available.

Decay adjusts the approximate time required for the algorithm’s reverb tail to drop to 1/1000th (-60
dB) of its initial amplitude. Size controls the size of the virtual room. Delay sets an additional predelay
time in milliseconds for the algorithm section.

The Freeze controls consist of two buttons, Freeze and Freeze In. Freeze disables any input to the
reverb engine and sets the algorithm’s decay time to infinite, so that reverb output will sustain
endlessly. When enabled, Freeze In adds the input signal to the frozen reverberation, leading to a
build-up of reverberated sound.

Each algorithm and their unique parameters are described in further detail below.

26.23.4.1 Dark Hall

The Dark Hall algorithm is a smooth and classic sounding algorithm suitable for most medium to long
sounding halls.

In addition to the shared parameters listed above, Dark Hall also provides the following:

•

•

•

•

•

Damping controls the amount of high-frequency filtering within the reverb algorithms. Higher
values result in darker reverberation sounds.
Mod controls the amount of movement within the algorithm’s reverb tail. Less modulation
produces less movement, and more modulation creates more movement with a chorusing effect,
while diminishing the effect of resonances.
Shape transforms the artificial space’s sonic characteristics from small and resonant to large
and diffused.
Bass X controls the crossover frequency of the low-end part of the reverb tail, which is scaled
using the Bass Mult control.
Bass Mult scales the decay time of the low-end of the reverb tail.

In Dark Hall mode, long decay times combined with extremely small Size values create metallic
gong-like resonances.

26.23.4.2 Quartz

The Quartz algorithm is a hall-like reverb with some audible echoes in the reverb’s tail. This reverb has
a very clear replication of the input in the early reflections and is well suited for voices, drums and
signals with clear transients, as well as making echoes.

In addition to the shared parameters listed above, Quartz also provides the following:

•

•

•

Damping controls the amount of high-frequency filtering within the reverb algorithms. Higher
values result in darker reverberation sounds.
Lo Damp controls the amount of low frequency filtering within the reverb algorithms. Higher
values result in brighter reverberation sounds.
Mod controls the amount of movement within the algorithm’s reverb tail. Less modulation
produces less movement, and more modulation creates more movement with a chorusing effect,
while diminishing the effect of resonances.

•

•

Diffusion controls the density of the algorithm’s reverb tail. Low values produce sparser tails,
while higher values produce denser tails.
Distance controls the virtual distance of reflections. Lower values put them closer to the listener
and increase their density while higher values place them farther away and increase the time
between echoes.

26.23.4.3 Shimmer

The Shimmer reverb algorithm is made from densely stacked diffuse delays with a pitch shifter in the
feedback. Low diffusion values result in a pure delay, while high diffusion values result in a dense and
lush artificial reverb. The Shimmer effect crossfades the pitch-shifted signal into the feedback, resulting
in tails that climb or descend in frequency.

In addition to the shared parameters listed above, Shimmer also provides the following:

•

•

•
•

•

Damping controls the amount of high-frequency filtering within the reverb algorithms. Higher
values result in darker reverberation sounds.
Mod controls the amount of movement within the algorithm’s reverb tail. Less modulation
produces less movement, and more modulation creates more movement with a chorusing effect,
while diminishing the effect of resonances.
Pitch adjusts the degree of pitch-shifting applied to the feedback signal in semitones.
Diffusion controls the density of the algorithm’s reverb tail. Low values produce sparser tails,
while higher values produce denser tails. Turn this below 10% for dub-like delay effects. This is
very fun to use on drums!
Shimmer adjusts the intensity of the Shimmer effect. When set to 0%, no pitch shifting is applied;
the level of the pitched signal is progressively more present as the percentage is increased.
When used on melodic material, setting Shimmer to 100% produces interesting pitch
harmonizations.

In Shimmer mode, the Size knob adjusts the distance between individual echoes on percussive
material.

26.23.4.4 Tides

The Tides algorithm uses a smooth reverb while modulating the output’s spectrum with a multiband
filter, creating rippling frequency band effects.

In addition to the shared parameters listed above, Tides also provides the following:

•

•
•
•

•

Damping controls the amount of high-frequency filtering within the reverb algorithms. Higher
values result in darker reverberation sounds.
Wave morphs the filter modulation waveform from noise (0%) to sine (50%) to square (100%).
Tide adjusts the intensity of texture created by the modulation of the reverb tail.
Phase adjusts the amount of offset between the modulation waveforms for the left and right
channel. At 180°, the channels will be perfectly out of phase.
Rate sets the rate of the modulation oscillator in beat divisions with Triplet, 16th, and Dotted
note value variations.

26.23.4.5 Prism

The Prism algorithm is a bright, unique and artificial-sounding diffuse reverb based on velvet
(spectrally flat) noise. This algorithm can easily be used as a “ghost” reverb, adding depth without
interfering with the source material. It is well suited for non-linear short decays on drums and transient
material but can be also used on more sustained sounds with longer decays to achieve a clean yet
digital sound.

In addition to the shared parameters listed above, Prism also provides the following:

•
•
•

Low Mult scales the decay time of the low-end of the reverb tail.
High Mult scales the decay time of the high-end of the reverb tail.
X over controls the crossover frequency between the low-frequency and high-frequency
portions of the reverb tail, which in turn adjusts the frequency content affected by the Low Mult
and High Mult parameters.

Tip: For a classic ’80s-style gated snare reverb, use smaller Decay and Size values.

26.23.5 EQ Section

Hybrid Reverb’s EQ Section.

The EQ section of Hybrid Reverb is found in the second tab of the device’s display. You can quickly
activate or deactivate it by clicking on its toggle button in the tab.

By default, the EQ is placed after both reverb engines in the signal chain; however, by toggling the
Pre Algo button, you can place the EQ before the algorithmic reverb, regardless of which reverb
routing you have chosen.

Four bands of control are provided to further shape the reverb signal. The low and high bands can be
toggled between pass filters and shelving EQs. While in low-pass or high-pass mode, the filters
provide a range of slopes, from a gentle 6 dB/octave to a steep 96 dB/octave. The two middle peak
EQs can cover the entire frequency range and can be used for anything from wide-band boosting to
semi-narrow cuts.

26.23.6 Output Section

Hybrid Reverb’s output section contains a final set of parameters to shape the device’s overall sound.

Stereo sets the stereo width of the wet signal. 0% yields a mono signal whereas values above 100%
create a widened stereo panorama.

The Vintage slider increasingly degrades Hybrid Reverb’s sounds by emulating lower sample rates
and bit-depths, as is common in vintage digital reverberation devices. Four presets can be used to
radically alter the overall sound: Subtle, Old, Older, and Extreme.

Bass Mono converts frequencies lower than 180 Hz of Hybrid Reverb’s output signal to mono, which
helps to make bass frequencies sound tighter.

The Dry/Wet control adjusts the balance between the processed and dry signals. Set it to 100%
when using Hybrid Reverb in a return track.

26.24 Limiter

The Limiter Effect.

The Limiter effect is a mastering-quality dynamic range processor that ensures that the output does not
exceed a specified level. Limiter is ideal for use on the Main track, to prevent clipping in digital-to-
analog converters. A limiter is essentially a compressor with an infinite ratio. For more information
about compression theory, refer to the Compressor section.

Limiter’s display contains the Ceiling control and the Gain Reduction meter. The Ceiling control sets the
absolute maximum level that Limiter will output. If your incoming signal level has no peaks that are
higher than the ceiling, no limiting will be applied by the device.

The Gain Reduction meter shows the amount of gain reduction being applied when the signal reaches
the ceiling or threshold.

The Link control defines how much of the gain reduction applied by Limiter is shared across its two
channels. These can be the left/right channels or the mid/side channels, depending on which Routing
Mode is selected. When set to 100%, limiting is applied to both channels whenever either requires
compression, ensuring a stable stereo image. When set to 0%, the channels are processed
independently, with different gain reduction applied to each channel. This can be useful when
working with signals where the left and right channels are separate, or to achieve creative effects,
such as a “wobble” in the stereo image.

You can use the Input Gain knob to the left of the display to boost or attenuate the incoming signal
level before limiting is applied to it.

Switching on the Maximize toggle below the Input Gain knob changes the Ceiling control to
Threshold, which allows you to adjust the signal’s dynamic range and loudness with a single control.
Lowering the Threshold amplifies the limiter stage output by the inverse of the Threshold value. Note
that the Input Gain knob becomes the Output control when Maximize is on, and sets the target output
level for the device.

The Release knob adjusts how long it takes for the device to stop applying limiting after the signal falls
below the ceiling or threshold. Fast release times make the output sound louder and punchier, while
slow release times add smoothness, though can also reduce the dynamic range. The Gain Reduction
meter helps to visualize the effect of the Release control: at faster release times you will see the meter
return to zero more quickly, while at slower release times the meter recovers more gradually, and
Limiter maintains compression for a longer time.

You can use the Auto toggle beneath the Release knob to activate auto-release. When on, Limiter
analyzes incoming audio and continuously updates its release time based on the signal’s
characteristics. Note that when auto-release is enabled, the Release control is deactivated.

The Lookahead control to the right of the display allows you to adjust the setting that determines how
quickly Limiter will respond to peaks that require compression. The lookahead time can be set to 1.5,
3, or 6 milliseconds. Shorter lookahead times allow for more compression but can increase distortion,
especially when applied to bass sounds. As the lookahead time affects Limiter’s attack time, longer
lookahead values are useful for catching very fast peaks. Note that lookahead introduces latency: the
longer the lookahead time, the higher the latency.

The Ceiling Mode toggles let you choose between three ceiling modes: Standard, Soft Clip, and True
Peak. Standard is the device’s default mode. Soft Clip introduces soft clipping when signals approach
the device’s ceiling level, which can add subtle color and punch to transients. When Soft Clip is on, an
LED appears above the mode toggles, and flashes to indicate that the signal is clipping. Finally, the
True Peak mode prevents inter-sample peaks.

You can use the Routing Mode toggles to determine how Limiter treats peaks that occur on only one
side of the stereo signal. In L/R mode, the left and right channels of the signal are compressed
independently. This allows the device to apply more compression, but with some distortion of the
stereo image. In M/S mode, Limiter encodes the signal to mid/side before the limiting stage, then
decodes it to stereo at the output stage. This can be useful for preserving the signal’s stereo image, but
results in higher latency.

Note that adding any further processing effects after Limiter may add gain. To ensure that your final
output will never clip, place Limiter as the last device in the Main track’s device chain and keep the
Main track’s volume below 0 dB.

26.25 Looper

The Looper Effect.

Looper is an audio effect based on classic real-time looping devices. It allows you to record and loop
audio, creating endless overdubs that are synced to your Set. If the Set is not playing, Looper can
analyze incoming audio and set Live’s tempo to match it. You can also predefine a loop length before
recording and Live’s tempo will adjust so that your loop fits into the specified number of bars.
Furthermore, audio can be imported to Looper to create a background for newly overdubbed
material, or exported from Looper as a new clip.

The top half of Looper’s interface is a large display area optimized for easy readability during
performance. During recording, the entire display area turns red. After recording, the display shows
the current position in the loop and the total loop length in bars and beats.

Looper’s transport buttons work in a similar way to other transport controls in Live. The Record button
records incoming audio until another button is pressed. This overwrites any audio currently stored in
Looper. Overdub continues to add additional layers of incoming audio that are the length of the

originally recorded material. The Play button plays back the current state of Looper’s buffer without
recording any new material. The Stop button stops playback.

The behavior of the transport controls changes depending on whether or not Live’s playback is
running. With the transport running, Looper behaves like a clip, and is subject to launch quantization
as determined by the Quantization chooser. When Live’s playback is stopped, Looper’s transport
engages immediately, regardless of the Quantization setting.

The Clear button erases Looper’s buffer. If you press Clear in Overdub mode while the transport is
running, the contents of the buffer are cleared but the tempo and length are maintained. Pressing
Clear in any other mode resets the tempo and length.

The Undo button erases everything that you’ve overdubbed since the last time Overdub was enabled.
Your original recording, and anything that was overdubbed in a previous pass, is preserved. After
pressing Undo, the button changes to Redo, which replaces the material removed by the last undo.

The large button below the transport controls is the Multi-Purpose Transport Button. As with the normal
transport buttons, this button’s behavior changes depending on Looper’s current playback state, and
whether or not material has already been recorded. If the buffer is empty, a single click starts
recording. If Looper is recording, overdubbing or stopped, a single click switches to play mode.
During playback, a click switches to overdub mode, allowing you to toggle back and forth between
overdub and playback via additional single clicks.

Quickly pressing the button twice stops Looper, from either play or overdub mode. Clicking and
holding the button for two seconds while in play mode activates Undo or Redo. Pressing and holding
for two seconds while stopped clears Looper’s buffer.

Diagram of Looper’s Multi-Purpose Transport Button Behavior.

Looper’s Multi-Purpose Transport Button is optimized for use with a MIDI footswitch. To assign a
footswitch, enter MIDI Map Mode, click the button and then press your attached footswitch. Then exit
MIDI Map Mode.

The Tempo Control chooser affects how Looper determines the tempo of recorded material:

•
•

•

None: Looper’s internal tempo is independent of Live’s global tempo.
Follow song tempo: The speed of Looper’s playback will be adjusted so that the recorded
material plays back at Live’s global tempo.
Set & Follow song tempo: Live’s global tempo will be adjusted to match the tempo of material
recorded into Looper. Any subsequent changes to Live’s global tempo will adjust the speed of
Looper’s playback so that the recorded material plays back at the new global tempo.

The Record Length chooser is used to set the length of recorded material. Its behavior changes
depending on whether or not Live’s global transport is running and, depending on the setting of the
Tempo Control chooser, can set Live’s global tempo:

•

•

Song running: If Looper’s Record Length chooser is set to the default ”x bars,” Looper will
record until you press another transport button. If you specify a fixed number of bars to record
by selecting another option in the chooser, Looper will record for the specified time and then
switch to Play or Overdub, as determined by the button next to this chooser.
Song not running: If Looper’s Record Length chooser is set to the default ”x bars,” Looper will
make a guess about the tempo of the material you’ve recorded as soon as you press Overdub,
Play or Stop. But this might result in a tempo that’s twice or half as fast as you’d like. If you first
specify a fixed number of bars, Looper’s tempo will adjust so that your recording fits into this
time.

The Song Control chooser determines how Looper’s transport controls will affect Live’s global
transport:

•
•

•

None means that Looper’s transport controls have no effect on Live’s global transport.
Start Song will start Live’s global transport whenever Looper enters Play or Overdub mode.
Looper’s Stop button has no effect on the global transport.
Start & Stop Song locks Live’s global transport to Looper’s transport controls. Entering Play or
Overdub mode will start Live’s transport, while pressing Looper’s Stop button will stop Live’s
transport.

Starting playback of Live’s transport via Looper will automatically adjust the playback position of any
apps that are connected via Ableton Link. This ensures that those apps remain tempo synced, and also
at the correct position in the musical phrase.

The ”×2” button doubles the length of Looper’s recording buffer. Any material that you’ve already
recorded will simply be duplicated. This allows you to, for example, record a series of one-bar ideas,
and then overlay a series of two-bar ideas. The length and tempo of Looper’s buffer is shown in the
display area.

Similarly, the ”÷2” button cuts the length of the current buffer in half. The material in the currently
playing half is kept, while the other half is discarded.

The ”Drag me!” area in the display allows you to export Looper’s buffer as a new audio file. You can
drag and drop to the browser or directly to a track, creating a new clip. The newly created clip’s
Warp Mode will be set to Re-Pitch by default. You can also drag audio files to the ”Drag me!” area,
which will replace the contents of Looper’s buffer. You can then use this material as a bed for further
overdubs, for example.

The Speed knob adjusts Looper’s playback speed (and thus pitch). The up and down arrow buttons to
the left are shortcuts to raise or lower the pitch by octaves (thus doubling or halving the playback
speed). These buttons are subject to the Quantization chooser setting.

Enabling the Reverse button plays the previously recorded material backwards. Any material that you
overdub after enabling Reverse will be played forward. Note that disabling Reverse will then swap
this behavior; the original material will play forward again, while the material that was overdubbed
while Reverse was enabled will play backwards. Engaging the Reverse button is subject to the
Quantization chooser setting.

Feedback sets the amount of previously recorded signal that is fed back into Looper when
overdubbing. When set to 100%, the previously recorded material will never decrease in volume.
When set to 50%, it will be half as loud with each repetition. Any changes to the Feedback amount
won’t take effect until the next repetition. Note that Feedback has no effect in Play mode; each
repetition will be at the same volume.

The Input -> Output chooser provides four options for monitoring Looper’s input:

•

•

•

•

Always allows the input signal to be heard regardless of Looper’s playing or recording state.
You’ll typically want to choose Always when using Looper as an effect in a single track.
Never means that the input signal will never be heard. You’ll typically want to choose Never
when using Looper as an effect in a return track, where it may be fed by send levels from a
variety of other tracks.
Rec/OVR means that the input is only audible when recording or overdubbing, but not when
Looper is in Play mode or stopped. This is useful for situations in which you are feeding audio to
multiple tracks, each containing its own Looper. If each of these Loopers is controlled with its
own foot pedal, you can switch the recording and playback state while playing an instrument,
without having to worry about monitor settings.
Rec/OVR/Stop allows the input signal to be heard except when Looper is in play mode. This is
similar to Beat Repeat’s Insert mode, and can be used to record material that can suddenly
interrupt your live playing.

26.25.1 Feedback Routing

Looper can be used as both a source and a target for internal routing to other tracks. This allows you
to, for example, create Looper overdubs that continually feed back through another track’s devices. To
set this up:

1.
2.
3.

Insert Looper on a track.
Record at least one pass of material into Looper.
Create another audio track.

4.

5.
6.
7.
8.

In the new track’s top Audio From and Audio To choosers, select the track containing the
Looper.
In the new track’s bottom Audio From and Audio To choosers, select ”Insert-Looper.”
Switch this track’s Monitoring to ”In.”
Add additional effects devices to the device chain of the new track.
Put Looper into Overdub mode.

Looper’s output will now be routed through the other track’s device chain and then back into itself,
creating increasingly processed overdub layers with each pass.

26.26 Multiband Dynamics

The Multiband Dynamics Effect.

The Multiband Dynamics device is a flexible tool for modifying the dynamic range of audio material.
Designed primarily as a mastering processor, Multiband Dynamics allows for upward and downward
compression and expansion of up to three independent frequency bands, with adjustable crossover
points and envelope controls for each band. Each frequency range has both an upper and lower
threshold, allowing for two types of dynamics processing to be used simultaneously per band.

26.26.1 Dynamics Processing Theory

To understand how to use the Multiband Dynamics device, it helps to understand the four different
methods of manipulating dynamics.

When we use the term “compression,” we’re typically talking about lowering the level of signals that
exceed a threshold. This is how Live’s Compressor works, and is more accurately called downward
compression because it pushes loud signals down, thus reducing the dynamic range. But it is also
possible to reduce a signal’s dynamic range by raising the levels of signals that are below a threshold.
This much-less-common form of compression is called upward compression. As you can see from this
diagram, employing either type of compression results in a signal with a smaller dynamic range than
the original.

Downward and Upward Compression.

The opposite of compression is expansion. A typical expander lowers the levels of signals that are
below a threshold. This is how Live’s Gate works, and is more accurately called downward expansion
because it pushes quiet signals down, thus increasing the dynamic range. It is also possible to increase
a signal’s dynamic range by raising the levels of signals that are above a threshold. Like upward
compression, this technique is known as upward expansion and is much less common. This diagram
shows that either type of expansion results in a signal with a larger dynamic range.

Downward and Upward Expansion.

To summarize:

•
•
•
•

Downward compression (common): make loud signals quieter
Upward compression (uncommon): make quiet signals louder
Downward expansion (common): make quiet signals quieter
Upward expansion (uncommon): make loud signals louder

The Multiband Dynamics device allows for all of these types of processing. In fact, because the device
allows for incoming audio to be divided into three frequency bands, and each band has both an

upper and lower threshold, a single instance of Multiband Dynamics can provide six types of
dynamics processing simultaneously.

26.26.2 Interface and Controls

The High and Low buttons toggle the high and low bands on or off. With both bands off, the device
functions as a single-band effect. In this case, only the Mid controls affect the incoming signal. The
frequency sliders below the High and Low buttons adjust the crossovers that define the frequency
ranges for each band. If the low frequency is set to 500 Hz and the high frequency is set to 2000 Hz,
then the low band goes from 0 Hz to 500 Hz, the mid band from 500 Hz to 2000 Hz and the high
band from 2000 Hz up to whatever your soundcard or sample rate supports.

Each band has activator and solo buttons. With the activator button disabled for a given band, its
compression/expansion and gain controls are bypassed. Soloing a band mutes the others. The Input
knobs boost or attenuate the level of each band before it undergoes dynamics processing, while the
Output knobs to the right of the display adjust the levels of the bands after processing.

The display area provides a way of both visualizing your dynamics processing and adjusting the
relevant compression and expansion behavior. For each band, the output level is represented by large
bars, while the input level before processing is represented by small bars. With no processing applied,
the input meters will be aligned with the top of the output meters. The scaling along the bottom of the
display shows dB. As you adjust the gain or dynamics processing for a band, you can see how its
output changes in comparison to its input.

As you move your mouse over the display, the cursor will change to a bracket as it passes over the
edges of the blocks on the left or right side. These blocks represent the signal levels under the Below
and over the Above thresholds, respectively. Dragging left or right on the edges of these blocks
adjusts the threshold level. Holding down Ctrl (Win) / Cmd (Mac) while dragging a threshold
will adjust the same threshold for all bands. Hold down Alt (Win) / Option (Mac) to
simultaneously adjust the Above and Below thresholds for a single band. Holding down Shift
while dragging left or right allows you to adjust the threshold of a single band at a finer resolution.

As you mouse over the middle of the block, the cursor will change to an up-down arrow. Click and
drag up or down to make the signal within the selected volume range louder or quieter. Holding
down Ctrl (Win) / Cmd (Mac) while dragging up or down will adjust the volume of the same
block for all bands. Hold down Alt (Win) / Option (Mac) to simultaneously adjust the Above
and Below volumes for a single band. Holding down Shift while dragging up or down allows you
to adjust the volume of a single band at a finer resolution. Double-clicking within the region resets the
volume to its default.

In technical terms, lowering the volume in the block above the Above threshold applies downward
compression, while raising it applies upward expansion. Likewise, lowering the volume in the block
below the Below threshold applies downward expansion, while raising it applies upward
compression. In all cases, you are adjusting the ratio of the compressor or expander.

The thresholds and ratios of all bands can also be adjusted via the column to the right of the display.
The ”T,” ”B” and ”A” buttons at the bottom right of the display area toggle between displaying the

Time (attack and release), Below (threshold and ratio) and Above (threshold and ratio) for each
band.

For the Above thresholds, Attack defines how long it takes to reach maximum compression or
expansion once a signal exceeds the threshold, while Release sets how long it takes for the device to
return to normal operation after the signal falls below the threshold.

For the Below thresholds, Attack defines how long it takes to reach maximum compression or
expansion once a signal drops below the threshold, while Release sets how long it takes for the
device to return to normal operation after the signal goes above the threshold.

With Soft Knee enabled, compression or expansion begins gradually as the threshold is approached.

The RMS/Peak switch also affects how quickly Multiband Dynamics responds to level changes. With
Peak selected, the device reacts to short peaks within a signal. RMS mode causes it to be less sensitive
to very short peaks and to begin processing only when the incoming level has crossed the threshold
for a slightly longer time.

The global Output knob adjusts the overall output gain of the device.

The Time control scales the durations of all of the Attack and Release controls. This allows you to
maintain the same relative envelope times, but make them all faster or slower by the same amount.

The Amount knob adjusts the intensity of the compression or expansion applied to all bands. At 0%,
each compressor/expander has an effective ratio of 1, meaning that it has no effect on the signal.

26.26.3 Sidechain Parameters

The Multiband Dynamics Device With Sidechain Section.

Normally, the signal being processed and the input source that triggers the device are the same
signal. But by using sidechaining, it is possible to apply dynamics processing to a signal based on the
level of another signal or a specific frequency component. To access the Sidechain parameters, unfold
the Multiband Dynamics window by toggling the

 button in its title bar.

Enabling the Sidechain button allows you to select any of Live’s internal routing points from the
choosers below. This causes the selected source to act as the device’s trigger, instead of the signal that
is actually being processed.

The Gain knob adjusts the level of the external sidechain’s input, while the Dry/Wet knob allows you
to use a combination of sidechain and original signal as the trigger. With Dry/Wet at 100%, the
device is triggered entirely by the sidechain source. At 0%, the sidechain is effectively bypassed. Note
that increasing the gain does not increase the volume of the source signal in the mix. The sidechain
audio is only a trigger for the device and is never actually heard.

The headphones button allows you to listen to only the sidechain input, bypassing the device’s output.
Since the sidechain audio isn’t fed to the output, and is only a trigger for the device, this temporary
listening option can make it much easier to set sidechain parameters and hear what’s actually making
the device work.

26.26.4 Multiband Dynamics Tips

Multiband Dynamics is a feature-rich and powerful device, capable of up to six independent types of
simultaneous processing. Because of this, getting started can be a bit intimidating. Here are some
real-world applications to give you some ideas.

26.26.4.1 Basic Multiband Compression

By using only the upper thresholds, Multiband Dynamics can be used as a traditional ”downward”
compressor. Adjust the crossover points to suit your audio material, then apply downward
compression (by dragging down in the upper blocks in the display or by setting the numerical ratios to
values greater than 1.)

26.26.4.2 De-essing

To remove ”harshness” caused by overly loud high frequency content, try enabling only the upper
band and setting its crossover frequency to around 5 kHz. Then gradually adjust the threshold and
ratio to apply subtle downward compression. It may help to solo the band to more easily hear the
results of your adjustments. Generally, de-essing works best with fairly fast attack and release times.

26.26.4.3 Uncompression

Mastering engineers are often asked to perform miracles, like adding punch and energy to a mix that
has already been heavily compressed, and thus has almost no remaining transients. Most of the time,
these mixes have also been heavily maximized, meaning that they also have no remaining headroom.
Luckily, upward expansion can sometimes help add life back to such overly squashed material. To do
this:

1.
2.
3.

Turn down the Input knob to provide some additional headroom.
Adjust the Above thresholds for the bands so that they’re below the highest peaks.
Add a small amount of upward expansion to each band. Be careful — excessive upward
expansion can make transients very loud.

4.

Carefully adjust the attack and release times for each band. Note that, unlike in typical
downward compression, very fast attack times will increase the impact of transients, while
slower times result in a more muffled sound.

Note: Adding a maximizer or limiter to boost gain after you’ve returned some peaks to your material
may simply destroy them again.

26.27 Overdrive

The Overdrive Effect.

Overdrive is a distortion effect that pays homage to some classic pedal devices commonly used by
guitarists. Unlike many distortion units, it can be driven extremely hard without sacrificing dynamic
range.

The distortion stage is preceded by a band-pass filter that can be controlled with an X-Y controller. To
define the filter bandwidth, click and drag on the vertical axis. To set the position of the frequency
band, click and drag on the horizontal axis. These parameters can also be set via the slider boxes
below the X-Y display.

The Drive control sets the amount of distortion. Note that 0% does not mean zero distortion!

Tone acts as a post-distortion EQ control. At higher values, the signal has more high-frequency
content.

The Dynamics slider allows you to adjust how much compression is applied as the distortion is
increased. At low settings, higher distortion amounts result in an increase in internal compression and
make-up gain. At higher settings, less compression is applied.

The Dry/Wet control adjusts the balance between the processed and dry signals. Set it to 100
percent if using Overdrive in a return track.

26.28 Pedal

The Pedal Effect.

Pedal is a guitar distortion effect. In combination with Live’s Tuner, Amp and Cabinet effects, Pedal is
great for processing guitar sounds. Pedal can also be used in less conventional settings, such as a
standalone effect on vocals, synths or drums.

The Gain control adjusts the amount of distortion applied to the dry signal. Note that 0% does not
mean zero distortion. It is recommended to dial the Gain back to 0% and slowly increase it until you
get the desired output level. When placed in front of Pedal in a device chain, Utility’s Gain parameter
can be used to lower the signal even further.

The global Output knob adjusts the overall output gain of the device.

You can choose between three different Pedal Types, each inspired by distortion pedals with their own
distinct sonic characteristics:

•

Overdrive: warm and smooth

•
•

Distortion: tight and aggressive
Fuzz: unstable, with a “broken amp” sound

Pedal has a three-band EQ that adjusts the timbre of the sound after the distortion is applied. The EQ
is adaptive, which means that the amount of resonance (or “Q”) increases as the amount of EQ boost
increases.

The Bass control is a peak EQ, with a center frequency of 100 Hz. This is useful for boosting the
“punch” in bass or drum sounds, or attenuating low frequencies of guitars.

The Mid control is a three-way switchable boosting EQ. The Mid Frequency switch sets the center
frequency and range of the Mid control. The center frequency is the middle of the frequency range
that the Mid control operates upon. The frequency range around this center value is narrower in the
lowest switch setting and wider in the higher setting. This is common in guitar pedals where it is normal
to make tight cuts and boosts at low frequencies, and wider cuts and boosts at high frequencies.

The center frequencies for the switch settings are:

•
•
•

Lowest setting, positioned on the left side: 500 Hz
Middle setting, positioned in the center: 1 kHz
Highest setting, positioned on the right side: 2 kHz

The Treble control is a shelving EQ, with a cutoff frequency of 3.3 kHz. This is useful for removing
harsh high frequencies (or boosting them, if that’s your cup of tea!).

Tip: For a more fine-grained EQ post-distortion, simply leave these controls in their neutral position
and instead use another EQ, such as EQ Eight.

The Sub switch toggles a low shelf filter that boosts frequencies below 250 Hz. You can use this in
conjunction with the Bass control by turning Sub on and setting the Bass to -100%, or turning Sub off
and setting the Bass to 100%.

The Dry/Wet slider adjusts the balance between the processed and dry signals.

Aliasing can be reduced by enabling Hi-Quality mode, which can be accessed via the device title
bar’s context menu. This improves the sound quality, particularly with high frequency signals, but there
is a slight increase in CPU usage.

26.28.1 Pedal Tips

26.28.1.1 Positioning Pedal in the Device Chain

The incoming signal will have an impact on how the distortion will respond. For example, adding a
Compressor before Pedal in the device chain will give a more balanced end result. On the other
hand, adding an EQ or filter with high gain and resonance settings before Pedal can yield a
screaming distortion effect.

26.28.1.2 Techno Kick

Choose a suitable kick with a long decay (e.g., Kit-Core 909, with decay turned up). Then, choose the
Distort pedal, activate the Sub switch, and dial in the Gain to your taste.

For added “whack”, move the Mid Frequency switch to the right-most position and increase the Mid
control. For more “thump”, you can increase the Bass control.

To reduce the “air”, decrease the Treble control.

26.28.1.3 Drum Group Fizzle

To add “fizzle” to a drum group, choose the Fuzz pedal, increase the Gain to 50% and make sure the
Sub switch is disabled.

Reduce the Bass and Mid controls to -100%, and adjust the Mid Frequency Switch to taste. Increase
the Treble to 100%.

Set the Output to -20dB. Then, turn the Dry/Wet slider down to 0% and slowly increase it until the
drums are fizzling to your taste.

26.28.1.4 Broken Speaker

Select the Fuzz pedal, and make sure the Sub switch is disabled. Turn down the Bass control
completely, and set the Treble to 25%.

Set the Mid control 100% and move the Mid Frequency switch to right-most position. Finally, set the
Gain control to 100%.

26.28.1.5 Sub Warmer

To add upper harmonics and warmth to a simple sub bass, choose the OD pedal, turn on the Sub
switch and turn up the Bass control. Then, slowly increase the Gain until the desired effect is reached.
You can then cut or boost the mid frequencies using the Mid control.

26.29 Phaser-Flanger

The Phaser-Flanger Effect.

Phaser-Flanger combines the functionalities of flanger and phaser effects into one device with
separate modes, and offers an additional Doubler mode. All modes can be used to create lush,
expressive sounds with a wide variety of tools and detailed options. Two LFOs and an envelope
follower provide plenty of modulation possibilities.

You can choose between the three modes in the display:

•

•

•

Phaser, with its wide range of frequency and modulation ranges, creates wandering notch
filters by feeding a phase-shifted version of the input signal back into the input. The phase
shifting is achieved using modulated all-pass filters and has a lush sound.
Flanger creates a continuously changing comb filter effect by adding a time-modulated
delayed signal with feedback to the input.
Doubler creates the effect of doubled tracks (multiple stacked versions of similar recording
takes) by adding time-modulated delayed signals to the input.

The display contains a visualization and the mode selector buttons. The visualization presents different
information depending on the mode you choose and the LFO Stereo Mode’s settings (described in
more detail below).

In Phaser mode, the visualization shows the number of notches and their spectral positions.

Phaser’s parameters can be adjusted in the lower portion of the display.

Notches increases or decreases the number of all-pass filters being used. Center chooses the center
frequency of the notches. Spread increases or decreases the distance between the notches by
adjusting the Q factor of the all-pass filters. Blend mixes the modulation routing between Center
Frequency and Spread, with Center Frequency at 0.0 and Spread at 1.0.

In Flanger mode, the visualization shows how the modulation signal is affecting the delay time, with
the left-most position equaling the value chosen in the Time parameter. As the visualization moves to
the right, the delay time decreases; as it moves to the left, it increases. Time adjusts the delay time of
the Flanger delay lines.

In Doubler mode, the visualization acts differently than in Flanger mode. Modulation in Doubler mode
is bipolar, meaning that, as the visualization moves to the right, the delay time increases; as it moves to
the left, it decreases. Time adjusts the delay time of the Doubler delay lines.

For finer control over the sound, you can unfold the device by toggling the
Flanger’s title bar to reveal further options for the main LFO, as well as a second LFO, an envelope
follower and a Safe Bass high-pass filter. Also shown is a visualization for the main LFO, in which its
rate, waveform and the phase relationships of the stereo channels are shown.

 button in Phaser-

The Phaser-Flanger Effect’s Unfolded View.

The main LFO’s speed is controlled by the Freq/Rate parameter, and can be either tempo-synced or
free-running. Use the Modulation Sync buttons to the left of the dial to switch between Frequency and
Sync Rate. When set to Hz, the corresponding Freq dial controls the LFO rate in Hertz; otherwise, the
Rate dial will sync the LFO with the song tempo.

Multiple waveforms for the main LFO are available and can be found in the LFO Waveform chooser.
These include Sine, Triangle (default), Saw Up, Saw Down, Rectangle, Random, and Random S&H
(Sample and Hold). Also included are Triangle Analog, Triangle 8, Triangle 16, which are described
below:

•

•
•

Triangle Analog is a low-pass filtered rectangular waveform which changes shape and
amplitude drastically for different LFO rates.
Triangle 8 divides a period of a normal triangular wave into eight discrete steps.
Triangle 16 divides a period of a normal triangular wave into 16 discrete steps.

The LFO Stereo Mode button switches between Phase and Spin modes, both of which allow
modulation of each stereo channel independently.

When Phase is chosen, adjusting the Phase value will change the phase relationship between the left
and right channels. At 180°, the phase of the left and right channels are completely inverted. This can
be seen in the LFOs visualization.

When Spin is chosen, adjusting the Spin value detunes the two LFO rates relative to each other. This
can be seen in the main display’s visualization.

Duty Cycle will change the time scale of the waveform’s period, compressing it towards either the front
of the cycle (100%) or the back of the cycle (-100%). At 0%, the time scale of the period is spread
equally across the entire cycle, leaving the waveform unaffected. This is similar to how Pulse Width
affects rectangular waveforms, and its effects can be seen in the waveform view of the main LFO. This
parameter doesn’t affect the noise-based Random and Random S&H modulation waveforms.

The second LFO always has a triangular waveform, and can be controlled using the LFO2 Mix and
LFO2 Freq/Rate parameters.

LFO2 Mix sets the amount of the LFO2 that is mixed with the main LFO. At 0%, only the main LFO is
active; at 100% only LFO2 is active.

The second LFO’s speed can be set as either free-running or tempo-synced by using the Modulation
Sync 2 toggle buttons. When free-running, the sync frequencies are shown in Hertz and can be
adjusted using the LFO2 Freq parameter. When tempo-synced, beat divisions are shown instead and
can be set using the LFO2 Rate parameter.

Global parameters available include Amount, Feedback, Output, Warmth and Dry/Wet. The
additional envelope follower and Safe Bass high-pass filter are accessible when the device is
unfolded.

Amount adjusts the amount of delay modulation that is applied to incoming signals and affects both
the main LFO and LFO2.

Feedback sets the amount of each channel’s output that is fed back to its input. Increasing this sounds
more extreme and tends to create a strong comb filtering effect, amplifying some frequencies and
attenuating others. In Doubler Mode, it will also create audible delays if playback is stopped. The
feedback signal can be inverted using the Ø button, which results in a “hollow” sound when
combined with high feedback values.

Caution: high feedback values in combination with certain settings can cause quick increases in
volume levels. Be sure to protect your ears and equipment!

Below the main LFO you will find an envelope follower. An envelope follower uses the amplitude from
an incoming audio signal and translates it to a modulation source.

To use the envelope follower, activate the Env Fol button and set the Envelope Amount value to a
value other than zero. Envelope Amount adjusts the intensity of the modulation caused by the
envelope follower. Negative values invert the phase of the envelope.

Attack and Release adjust the attack and release portions of the envelope follower’s envelope.
Shorter Attack times cause the envelope follower to act more quickly, while longer times delay its
onset. Shorter Release times cause the envelope follower to stop its effect faster than longer Release
times.

Safe Bass is a high-pass filter, effectively reducing the effect on signal components below the
specified frequency. The applicable range is from 5 Hz to 3000 Hz. This can make mixing certain
bass-heavy material easier.

Output sets the amount of gain applied to the processed signal. The Warmth control adds slight
distortion and filtering for a warmer sound. The Dry/Wet control adjusts the balance between the
processed and dry signals. Set it to 100% when using Phaser-Flanger in a return track.

26.30 Redux

The Redux Effect.

The Redux effect has a variety of parameters for creating a wide range of jagged and edgy sounds.
You can radically mangle any source material, with effects ranging from harsh distortion and digital
aliasing artifacts to warm, fat 8-bit grit. Extra noise and stereo width can be added to the
downsampling process, while filtering further transforms the sound. The quantizer’s amplitude curve
can also be changed to allow both subtle and drastic bitcrushing.

Redux makes use of two different digital signal manipulation techniques: downsampling and bit
reduction.

26.30.1 Downsampling

The downsampling controls are available on the left side of the device. Using Redux’s downsampler
without any filters engaged introduces inharmonic frequency content into the spectrum. The frequency
range of the added content is dependent upon the relationship between the frequency content of the
material and the sample rate chosen in the device.

Rate sets the sample rate to which the signal is degraded. Lower values result in increased imaging
and more inharmonic tones.

Jitter adds noise to the downsampler’s clock signal, which introduces randomness to the
downsampling process. This results in a noisier sound, as well as increased stereo width.

The Filter section has both a Pre and a Post setting. Enabling the Pre button engages a filter before
downsampling, which reduces the bandwidth of the signal processed by downsampling. When Jitter
is in use, it also reduces the stereo width of the signal.

The Post button engages a low-pass filter after the downsampling process, which reduces imaging.
The Post filter frequency can be adjusted using the Post-Filter Octave slider. The number shown
represents the number of octaves above or below half of the frequency shown in the Rate parameter.

26.30.2 Bit Reduction

The bit reduction controls are available on the right side of the device. Bit reduction decreases the
number of bits used to represent the digital signal, reducing dynamic range while adding distortion
and noise. At extreme settings, all original dynamics are lost and sounds are reduced to jagged
square waves.

The Bits control reduces the number of bits being used. The value shown represents the number of bits
used to encode the output signal. Reducing this value increases noise and distortion while reducing
dynamic range.

Shape varies the shape of the quantizer’s characteristic curve. Higher values produce a finer
resolution for smaller amplitudes, meaning that subtle signal components will be less affected than
louder ones. The total amount of distortion produced with different Shape settings will depend upon
the dynamic range of the input signal.

Enabling the DC Shift button applies an amplitude offset before the quantization process. This
significantly changes the sound of the quantization distortion, especially when Bits is set to lower
values, increasing volume and adding crunch!

The Dry/Wet control adjusts the balance between the processed and dry signals. Set it to 100%
when using Redux in a return track.

26.31 Resonators

The Resonators Effect.

This device consists of five parallel resonators that superimpose a tonal character on the input source.
It can produce sounds resembling anything from plucked strings to vocoder-like effects. The resonators
are tuned in semitones, providing a musical way of adjusting them. The first resonator defines the root
pitch and the four others are tuned relative to this pitch in musical intervals.

The input signal passes first through a filter, and then into the resonators. There are four input filter
types to select from: low-pass, band-pass, high-pass and notch. The input filter frequency can be
adjusted with the Frequency parameter.

The first resonator is fed with both the left and right input channels, while the second and fourth
resonators are dedicated to the left channel, and the third and fifth to the right channel.

The Note parameter defines the root pitch of all the resonators ranging from C-1 to C5. It can also be
detuned in cents using the Fine parameter. The Decay parameter lets you adjust the amount of time it
takes for the resonators to be silent after getting an input signal. The longer the decay time, the more
tonal the result will be, similar to the behavior of an undamped piano string. As with a real string, the
decay time depends on the pitch, so low notes will last longer than higher ones. The Const switch
holds the decay time constant regardless of the actual pitch.

Resonators provides two different resonation modes. Mode A provides a more realistic sounding
resonation, while Mode B offers an effect that is especially interesting when Resonator I’s Note
parameter is set to lower pitches.

The brightness of the resulting sound can be adjusted using the Color control.

All of the resonators have an On/Off switch and a Gain control. A resonator that is turned off does
not need CPU. Turning off the first resonator does not affect the other ones.

Resonators II through V follow the Note parameter defined in Resonator I, but they can each be
individually transposed +/- 24 semitones using the Pitch controls and detuned in cents using the
Detune controls.

The output section features the obligatory Dry/Wet control and a Width parameter that affects only
the wet signal and blends the left and right outputs of Resonators II-V into a mono signal if set to zero.

26.32 Reverb

The Reverb Effect.

Reverb is an audio effect that simulates the acoustic properties of audio as it echoes throughout a
physical space.

In the real world, reverberation exists as a product of sound waves that reflect off of rigid surfaces in
an environment and the subsequent tonal shaping of these waves by absorbent materials within their
trajectory. In a digital context, however, this phenomenon is approximated with a combination of
filters and modulated delay lines.

The Reverb device provides granular control of all of these factors in order to create unique spaces for
audio to travel through that range from intimate recording rooms to massive canyons, and everything
in between.

26.32.1 Input Filter

Reverb’s Input Filter Section.

The input signal passes first through low and high cut filters, whose X-Y controller allows changing the
band’s center frequency (X-axis) and bandwidth (Y-axis). The filters can also be controlled using the
sliders located below the X-Y controller. Either filter may be switched off when not needed to save
CPU power.

26.32.2 Early Reflections

Reverb’s Early Reflections Section.

These are the earliest echoes that you hear after they bounce off a room’s walls, before the onset of
the diffused reverberation tail. Their amplitude and distribution give an impression of the room’s
character.

Spin applies modulation to the early reflections. The Amount and Rate sliders control the amount and
rate of these modulations respectively. A higher Amount setting tends to provide a less-colored (more
spectrally neutral) late diffusion response. If the modulation rate is too high, doppler frequency shifting
of the source sound will occur, along with surreal panning effects. Spin may be turned off, using the
associated switch, for modest CPU savings.

The Shape control sculpts the prominence of the early reflections, as well as their overlap with the
diffused sound. With small values, the reflections decay more gradually and the diffused sound occurs

sooner, leading to a larger overlap between these components. With large values, the reflections
decay more rapidly and the diffused onset occurs later. A higher value can sometimes improve the
source’s intelligibility, while a lower value may give a smoother decay.

26.32.3 Diffusion Network

Reverb’s Diffusion Network Section.

The Diffusion Network creates the reverberant tail that follows the early reflections.

High and low shelving filters provide frequency-dependent reverberation decay. The high-frequency
decay models the absorption of sound energy due to air, walls and other materials in the room
(people, carpeting and so forth). The low shelf provides a thinner decay. Each filter may be turned off
to save CPU consumption.

The Diffusion and Scale parameters provide additional control over the diffusion’s density and
coarseness, and, when the room size is extremely small, have a large impact on the coloration
contributed by the diffusion.

26.32.4 Chorus

Reverb’s Chorus Section.

The Chorus section adds a little modulation and motion to the diffusion. You can control the
modulation Amount and Rate, or deactivate it altogether.

26.32.5 Global Settings

Reverb’s Global Settings.

Predelay controls the delay time, in milliseconds, before the onset of the first early reflection. This
delays the reverberation relative to the input signal. One’s impression of the size of a real room
depends partly on this delay. Typical values for natural sounds range from 1 ms to 25 ms.

The Smooth chooser specifies the behavior of the Size parameter when its value is adjusted. If set to
None, the Diffusion Network’s delay times are changed immediately, which can cause artifacts when
changing the Size value. If set to Slow or Fast, new delay times are updated over a specific time
period, which results in a smoother sound when transitioning between values.

The Size parameter controls the room’s volume. At one extreme, a very large size will lend a shifting,
diffused delay effect to the reverb. The other extreme — a very small value — will give it a highly
colored, metallic feel.

The Decay control adjusts the time required for this reverb tail to drop to 1/1000th (-60 dB) of its
initial amplitude.

The Freeze control freezes the diffuse response of the input sound. When on, the reverberation will
sustain almost endlessly. Flat bypasses the high and low shelf filters when Freeze is on. If Flat is off, the
frozen reverberation will lose energy in the attenuated frequency bands, depending on the state of the
high and low shelving filters. Cut modifies Freeze by preventing the input signal from adding to the
frozen reverberation; when off, the input signal will contribute to the diffused amplitude.

The Stereo control determines the width of the output’s stereo image. At the highest setting of 120
degrees, each ear receives a reverberant channel that is independent of the other (this is also a
property of the diffusion in real rooms). The lowest setting mixes the output signal to mono.

The Density chooser controls the tradeoff between reverb quality and performance. Sparse uses
minimal CPU resources, while High delivers the richest reverberation.

26.32.6 Output

Reverb’s Output Section.

At the reverb output, you can vary the amplitude of reflections and diffusion with the Reflect and
Diffuse controls and adjust the effect’s overall Dry/Wet mix.

26.33 Roar

The Roar Effect.

Roar is a saturation and coloration device with up to three processing stages and a range of flexible
routing configurations. Its selection of non-linear shaper curves and filters can be combined to
produce a wide variety of saturation types, from targeted warmth to sweeping harmonic motion or
glitchy blasts of noise. Roar’s feedback controls and built-in compressor add a further layer of
distinctive possibility to the device, which can produce sounds unlike any other instrument or effect
currently available in Live.

26.33.1 Input Section

Roar’s Input Section.

The Drive knob sets the level of the signal being input into Roar before the gain stages. It can be used
to quickly add or remove distortion without having to adjust individual Shaper Amount controls across
multiple gain stages, for example, or to modify an input signal to ensure a preset behaves as
expected.

The Tone Amount knob changes the input signal’s balance of high and low frequencies. When set to
positive values, high frequencies are boosted and low frequencies are attenuated. When set to
negative values, low frequencies are boosted and high frequencies are attenuated.

The Tone Frequency slider sets the frequency of the low shelving filter used by the Tone Amount
control.

Adjusting Roar’s Tone parameters has noticeable effects on the timbre of its gain stages, as these
follow the Input section in Roar’s processing chain. Dialing in positive values with the Tone Amount
knob can help attenuate low-frequency content in guitars or basses, for example, to avoid muddy
sounds when using large amounts of distortion.

The Color Compensation toggle next to the Tone Amount control applies a mirrored version of the
Tone filter to the output of Roar’s distortion stages. When active, Tone values are attenuated before the
shaper and boosted after it, giving you more control over the gain stage processing. Activating the
Color Compensation toggle with negative Tone values is a helpful trick for saturating drums without
affecting low end frequency impact, for example.

The Routing Mode panel lets you choose from six routing types: Single, Serial, Parallel, Multi Band,
Mid Side, and Feedback. Apart from Single and Multi Band modes, each routing mode has a Blend
control that allows you to control the blend between its two gain stages.

Serial mode processes the input signal using two concatenated shapers. The Blend control blends
between the sound of Stage 1 and the sound of Stages 1 and 2 combined.

Parallel mode processes the input signal using two independent shapers. The Blend control blends
between the sound of Stage 1 and the sound of Stage 2. To experiment with this mode, try selecting
two noticeably different Shaper Curves (like Half Wave Rectifier and Fractal) and modulating the
Blend control so that Roar’s sound shifts continuously from one to the other.

Multi Band mode splits the frequency spectrum into three bands (Low, Mid and High) that can each
be processed independently. Two Crossover Filters (Low and High) let you define the crossover
frequency between the three bands. This mode serves a variety of applications, including drum
processing and adding saturation to entire mixes.

Mid Side mode processes the input signal’s mono and stereo signals independently. This mode is
useful for enhancing a signal’s stereo image without compromising the sound of the signal at the
center of the stereo field.

Feedback mode processes the input signal and its feedback independently, which can create unusual
tones or transform Roar into a distinctive delay. Try modulating Roar’s Shaper Amount with an
envelope to produce saturation that has a shuffled delay effect, for example, or subtly offsetting
Shaper Bias to create delays that degrade over time.

26.33.2 Gain Stage Section

Roar’s Gain Stage Section.

Each routing mode has its own set of gain stages, which can be turned on or off independently using
the Stage toggles in the Gain Stage tabs.

Gain Stage tabs all have the same three controls: Shaper Amount, Shaper Bias, and Filter Frequency.
Shaper and Filter Types can be selected from their corresponding drop-down menus at the bottom of
each Gain Stage tab.

The Shaper Amount control sets the amount of saturation applied to the input signal. You can also click
and drag the shaper waveform in the Shaper Visualization display to modify this parameter. Distortion
occurs when the input signal reaches non-linear portions of the visualized curve.

The Shaper Bias control offsets the signal and creates asymmetrical distortion. At higher settings, it can
emulate the sound of a broken circuit. At more extreme settings, it will cause the signal to go
completely quiet.

The Shaper Type drop-down menu under the Shaper Visualization display has twelve curves to
choose from:

Soft Sine uses a sinusoidal curve to add smooth, warm saturation to the input signal. This shaper curve
tends to produce pleasant, analog-style distortion even when pushed to extreme levels.

Digital Clip applies a hard clipping curve to the input signal. It produces harsh, higher-order
harmonics when the input signal reaches the curve’s extremities.

Bit Crusher produces the characteristic distortion that occurs when quantized amplitudes are applied
to an input signal, similar to Live’s Redux device. Increasing the Shaper Amount reduces the number of
bits used for quantization and intensifies the effects of the bit crusher’s built-in compander. This curve
works well with bias modulation and produces very obvious changes in quieter signals.

Diode Clipper this type is a virtual analog clipping circuit emulation. It sounds smooth and warm like
the Soft Sine curve, but with attenuated high-end frequencies.

Tube Preamp models the soft, analog saturation of a tube preamp. It preserves a signal’s transients
and dynamics even when the Shaper Amount is set to higher levels.

Half Wave Rectifier and Full Wave Rectifier produce distinctive, waveshaper-style effects. Half Wave
Rectifier applies completely asymmetrical distortion to the input signal, which works well for adding
crunch to drum sounds. Full Wave Rectifier shifts the signal up by an octave, which works well for
adding harmonic depth to certain synth sounds.

Polynomial shifts between a sinusoidal curve and more complex waveforms. This shaper curve lends
itself well to modulation and to producing metallic sounds.

Fractal introduces a large of amount of high-end harmonics to the input signal.

Tri Fold this type is a triangular wavefolder. Like Fractal, it adds a large amount of high-end harmonics
to the input but achieves even harsher, more distorted results.

Noise Injection applies stereo noise followed by smooth distortion to the input signal. This curve works
well for producing smooth saturation that also has some dirt and grit.

Shards continuously changes the slope of its stereo curve segments to rhythmically break apart the
input signal.

Shapers can also be turned on or off via the toggle at the bottom of the Shaper Visualization display.

The Shaper Level control can be used to compensate for changes in output level produced as the
shaper curve is modified.

Filter Frequency adjusts the filter’s cutoff frequency. If the Pre toggle has been activated, the filter is
applied before the Shaper stage. When the Filter Frequency is changed with Pre activated, the filter
doesn’t affect the harmonics produced by the shaper.

There are eight filter types to choose from: low-pass, band-pass, high-pass, notch, peak, morph,
comb, and resampling. The Comb filter creates a series of notches across the frequency spectrum.
When its cutoff is modulated, this filter type can produce flanger-like effects. The Resampling filter
produces sample-rate reduction artifacts, similar to Live’s Redux device.

Apart from the Resampling filter, each filter has a dedicated Resonance control. The Peak filter has a
Filter Peak Gain control for boosting or attenuating a specific frequency range. The Morph filter has a
Morph control for setting its filter shape.

26.33.3 Modulation Section

To display Roar’s modulation parameters, click on the toggle in the Modulation panel. This will bring
up the Mod Sources and Matrix tabs.

Roar’s Modulation Toggle.

Roar’s Modulation Section.

The Mod Sources tab has four modulation sources to choose from: LFO 1, LFO 2, Env, and Noise.

Each LFO has five waveforms: three bipolar waveforms (sine, triangle, square) and two unipolar ramp
waveforms (up or down).

LFOs can be set to Free, Synced, Triplet, Dotted, or Sixteenth rates using the Mode drop-down menu.
Rate speed can be set in Hertz or tempo-synced and can be modified by clicking and dragging a
given rate up or down. Morph and Smooth controls can be changed in real time or modulated to
further sculpt LFO shapes.

The Env tab’s envelope follower generates a modulation signal based on Roar’s input signal. Attack,
Release, Threshold, Gain, Frequency, and Width controls let you hone in on the element you’d like to
isolate, even in busy sound sources. When activated, the Envelope Input Listen toggle plays back the
input signal only. Note that the Envelope Follower’s filter only affects what the envelope reacts to, not
Roar’s output signal.

The Envelope Follower is particularly useful as a modulation source in Roar’s Modulation Matrix. Try
setting it to follow a snare sound in a drum loop, for example, and have it modulate Roar’s Dry/Wet
balance or its Shaper Amount each time the snare hits.

The Noise modulation source includes four different noise types: Simplex, Wander, S & H, and Brown.
Noise curves can be set in Hertz or tempo-synced and can be smoothed like Roar’s LFO curves.

Simplex and Wander both generate smoothed random signals, with different random value
interpolation algorithms used to produce different signal dynamics. Simplex uses interrate modulation,
which produces a more irregular value interval than Wander. These types of noise are useful for
introducing small, random, organic-style changes in Roar’s output signal, especially when set to low
rates.

S & H (Sample and Hold) generates a random constant value that changes to a new random value at
an interval determined by the Noise Rate. This is useful for creating stepped random modulation
patterns in Roar’s output signal.

Brown produces low-pass filtered white noise, which is useful for producing a constant noise floor or
for adding crackles and hissing to Roar’s output signal.

The Matrix tab lets you assign modulation sources to modulation targets within the device. Clicking a
parameter while the Matrix tab is open will set it as a modulation target. Modulation sources are
listed horizontally and modulation targets are listed vertically. Click and drag a cell up or down to
apply modulation between parameters.

The Global Modulation Amount slider can be dragged up or down to increase or decrease the
modulation being applied globally. Clicking the X button will erase all modulation applied by the
Modulation Matrix.

The Modulation Matrix can also be expanded using the toggle in the device header. When
expanded, the device’s gain stages are all visible at once, as are all of the modulation sources and
targets in the Modulation Matrix.

Roar’s Expanded Matrix.

26.33.4 Feedback Section

Roar’s Feedback Section.

The Feedback section is one of Roar’s most distinctive features. Feeding Roar’s signal back into itself
can add a new layer of ringing, otherworldly tones and textures to your sound.

The Feedback Mode drop-down lets you choose between five feedback modes: Time, Synced, Triplet,
Dotted, and Note. Synced and Time modes let you use Roar’s Feedback as a delay. Note mode lets
you set the feedback’s ring to a specific pitch.

The Feedback Amount knob sets the amount of signal being fed back into Roar’s input. Because a
compressor is present in Roar’s feedback loop, loud signals will temporarily attenuate the amount of
feedback being generated as gain reduction is applied by the compressor.

When the Feedback Invert toggle is turned on, the phase of Roar’s feedback signal is inverted. The
phase cancelation effect that occurs when this inverted signal is fed back into the original creates
another layer to experiment with in Roar’s processing chain.

When the Feedback Gate toggle is turned on, Roar’s feedback automatically fades out when an input
signal is no longer being sent into the device. When turned off, Roar’s feedback continues indefinitely.

The Feedback Filter Frequency slider sets the center frequency of the band-pass filter used to process
Roar’s feedback. The Feedback Filter Width slider adjusts the filter’s bandwidth.

26.33.5 Global Section

Roar’s Global Section.

The Compression Amount knob sets the amount of compression being applied to the output signal,
and thereby to the signal being fed back into Roar.

When the Compressor Sidechain HP Filter toggle is turned on, a high-pass filter is applied to the
analysis signal used by the compressor’s sidechain. This is useful for lowering the amount of gain
reduction generated by the compressor’s response to low frequency signals.

The Output Gain knob sets the level of the wet signal being output, which is followed by a hard
clipping stage and then fed into the Dry/Wet stage. This parameter is useful for compensating level
changes produced by the Drive or Shaper Amount knobs.

The Dry/Wet slider adjusts the balance between the dry and wet signal being output by Roar.

26.34 Saturator

The Saturator Effect.

Saturator is a waveshaping effect that can add that missing dirt, punch or warmth to your sound. It
works by applying non-linear shaping to the input signal, with results ranging from soft saturation to
intense coloration.

Saturator shapes the incoming signal by mapping each individual value in the signal to a new value
according to a selected shaping curve. Because this is usually a non-linear process, the incoming
signal is dynamically reshaped based on its level at each moment in time.

You can select the curve used for shaping the input signal from the Curve Type chooser. There are
eight types to choose from: Analog Clip, Soft Sine, Bass Shaper, Medium Curve, Hard Curve, Sinoid
Fold, Digital Clip, and Waveshaper.

The available curve types offer various shaping characteristics. Digital Clip applies immediate, hard
clipping when exceeding the clipping point, while Analog Clip introduces a smoother transition
around the clipping point. These curves remain linear for signal levels below the clipping point. The
Soft Sine, Medium Curve, and Hard Curve types apply saturation with different sonic characteristic.
Sinoid Fold is a wavefolding type — as the input signal gets louder, the output folds over itself,
producing unusual textures.

The Bass Shaper curve is somewhat similar to Analog Clip, but presents a smoother harmonic
spectrum when driving low frequency signals with high gain. This makes it ideal for processing low-
end signals like 808 kick drums and synth basslines.

Bass Shaper includes an additional Bass Shaper Threshold control, which sets the threshold for the
curve from 0 to -50 dB. The curve remains linear when the input signal is below the threshold but
smoothly starts to clip once the signal exceeds the threshold. This allows you to move continuously
from one form of clipping to another: low threshold values produce soft clipping and high threshold
values produce hard clipping. Low threshold values work best for bass signals, especially when
combined with high Drive values.

The most dramatic signal shaping effect can be created by selecting the Waveshaper curve. This type
has its own dedicated set of controls, which are accessible by clicking the Toggle Expanded View
button in the device title bar; you can read more about how these parameters affect the signal in the
dedicated section below.

The Shaper Curve display both helps to visualize Saturator’s shaping curve and shows the input signal
in relation to the selected curve type in real time. Saturation occurs when the input signal reaches the
non-linear sections of the curve.

You can select a post-clipping stage for all the curve types using the Post Clip Mode chooser below
the Shaper Curve display. When Soft Clip or Hard Clip is selected, Saturator’s output will never
exceed the level set by the Output control. This is particularly useful for controlling any additional
boost created by negative Color values.

The Color toggle enables the device’s two color filters, which produce a color curve visualized in the
device’s expanded view. The color filters adjust an EQ curve that is first applied before the shaper,
then applied again, inverted, after the shaper. This allows you to, for example, remove bass
frequencies before the shaper, so that only mid/high frequencies are saturated and the energy of the
bass is maintained in the output.

You can use the Amt Lo slider to adjust the amount of saturation applied to low frequencies. Negative
values reduce the overall saturation applied to low frequencies, while positive values increase it.

The Drive control adjusts the gain applied to the input signal before it is processed by Saturator. You
can see how much this parameter is affecting the input signal in the device’s Shaper Curve display.

The Output control attenuates the signal level of Saturator’s final output. When Soft Clip is activated in
the Post Clip Mode chooser, Saturator will also apply an instance of the Analog Clip curve to the
device’s output.

The Dry/Wet control sets the balance between dry and processed signals in Saturator’s output. Set it
to 100% when using Saturator in a return track.

The Color Curve display in the expanded view shows a visualization of the curve being applied by
the device’s two color filters.

The Color Curve Display and Color Filter Parameters.

Below the display, there are three more controls for shaping Saturator’s color filters. Use the Amt Hi
slider to adjust the amount of saturation applied to the specified frequency range via the second filter.
Positive values add more saturation, while negative values decrease it. The Frequency slider can be
used to adjust the center frequency affected by the second color filter, while Width determines the
overall range of frequencies affected by it.

You can adjust the color filter parameters by clicking and dragging the handles in the Color Curve
display — dragging the first handle adjusts the Amt Lo parameter, while dragging the second handle
adjusts the Amt Hi or Frequency parameters, depending on whether you’re dragging the handle
horizontally or vertically.

26.34.0.1 Saturator’s Waveshaper Controls

When you select the Waveshaper curve type, six additional parameters become active in the
expanded view.

The Waveshaper Controls.

The Waveshaper controls influence the device’s signal shaping functions in the following ways:

•

Drive determines how much the Waveshaper curve’s parameters affect the input signal. At 0%,
these parameters have no effect on the Waveshaper curve. At 100%, these parameters fully
shape the curve.

•
•

•

•

•

Curve adds mostly third-order harmonics to the input signal.
Depth controls the amplitude of a sine wave that is superimposed onto the Waveshaper curve.
Increasing the value raises the amplitude of the sine wave, making its effect on the shaping
curve more pronounced. At 0%, the sine wave has no influence.
Linear works with the Curve and Depth parameters to alter the linear portion of the
Waveshaper curve.
Damp flattens any signals near the center of the waveform. It functions like an ultra-fast noise
gate.
Period determines the density of ripples in the superimposed sine wave in relation to the Depth
control.

26.34.0.2 Context Menu Options for Saturator

Two additional modes can be enabled in Saturator’s context menu: Hi-Quality and Pre-DC Filter. The
Hi-Quality mode reduces aliasing and improves sound quality (especially with high frequency
signals), at the cost of a slight increase in CPU usage. The Pre-DC Filter mode activates a DC filter at
Saturator’s input stage, which is useful for removing DC offsets from audio that contains them.

26.35 Shifter

The Shifter Effect.

Shifter is a multi-purpose pitch and frequency-shifting audio effect that can be used to add ring
modulation to incoming audio or to shift the pitch or frequency of audio in real time.

26.35.1 Tuning and Delay Section

Shifter’s Tuning and Delay Section.

The Coarse and Fine knobs adjust the pitch or frequency in the given value, depending on which shift
mode (explained in the Shifter Mode section) is selected.

Enabling the Wide button inverts the polarity of the Spread value for the right channel, creating a
stereo effect. This means that increasing the Spread value will shift the frequency down in the right
channel while shifting it up in the left. Note that Wide has no effect if the Spread value is set to 0.

In Pitch mode, the Window slider adjusts the window size used by the algorithm. Low frequency
signals often sound best with longer window sizes, while high frequencies often sound best with
shorter window sizes. Tone cuts the high frequencies of the delay’s feedback path.

Enabling the Delay button adds delay time that can be set using the slider control in Hertz or beat-
synced divisions, depending on which Delay Mode button you select. The Delay Feedback knob sets
the amount of the output that is fed back to the input of the delay.

26.35.2 LFO Section

Shifter’s LFO Section.

You can modulate the left and right stereo channels using Shifter’s LFO.

In the LFO waveform display, you can set the Duty Cycle and Phase/Spin/Width controls. Duty
Cycle sets the duty cycle of the LFO waveform. Phase adjusts the offset between the waveforms for the
left and right channel. At 180° the LFOs will be perfectly out of phase. Depending on the LFO
waveform or the Rate parameter, Phase may be replaced by a Spin or Width control, as explained
below.

When the Rate parameter (as described in further detail below) is set to beat-synced time divisions,
you will see the Offset parameter next to the Phase parameter, which shifts the starting point of each
LFO along its waveform.

There are several different LFO waveforms to choose from the LFO drop-down menu: Sine, Triangle,
Triangle Analog, Triangle 8, Triangle 16, Saw Up, Saw Down, Rectangle, Random, and Random
S&H.

The LFO waveforms Sine, Triangle, Triangle Analog, Triangle 8, Triangle 16, Saw Up, Saw Down, and
Rectangle can also be set to Spin instead of Phase. Spin detunes the two LFO speeds relative to one
another.

The LFO waveforms Random and Random S&H can only be set to Phase and Width, respectively.
Width adjusts the Stereo width of the random LFO waveform. At 0%, the waveform is identical for the
left and right channels. At 100%, the waveform is fully stereo, peaks on the left will correspond to
valleys on the right and vice versa.

LFO modulation is controlled with the Rate parameter, which can be set in Hertz or synced to the song
tempo and set in meter subdivisions (e.g. sixteenth notes). The Amount parameter sets the amount of
LFO modulation that is applied to incoming signals.

26.35.3 Envelope Follower Section

Shifter’s Envelope Follower.

Shifter’s envelope follower uses the amplitude from an incoming audio signal and translates it to a
modulation source.

The Envelope Attack sets how quickly the envelope follower responds to rising input levels and the
Envelope Release sets how quickly the envelope follower responds to falling input levels.

The Env Fol button switches on Shifter’s envelope follower. The Amount adjusts the intensity of the
envelope follower’s modulation. The Amount value can be set in semitones in Pitch mode or in Hertz in
the Freq and Ring modes.

26.35.4 Shifter Mode Section

The Shifter Mode Section.

Three different Shifter Mode button switches are available: Pitch, Freq, and Ring.

Pitch mode adjusts the pitch of incoming audio up or down by a user-specified amount in semitones
(Coarse tuning) and cents (Fine tuning).

Freq mode moves the frequencies of incoming audio up or down by a user-specified amount in Hertz.
Small amounts of shift can result in subtle tremolo or phasing effects, while large shifts can create
dissonant, metallic sounds.

In Ring mode, the user-specified frequency amount in Hertz is added to and subtracted from the input.

Drive enables a distortion effect, and the slider below it controls the level of the distortion. Note: Drive
is only available in Ring mode.

The Dry/Wet knob sets the balance between the dry and processed signals at Shifter’s output.

26.35.5 Sidechain Parameters

Shifter’s Sidechain Parameters.

To access the Sidechain parameters, unfold the Shifter window by toggling the triangle button on the
left of the title bar. There are two Pitch Modes available that determine how the pitch or frequency is
set: Internal and MIDI. In Internal mode, the pitch or frequency is set by Shifter’s Coarse and Fine
knobs. In MIDI mode, the pitch or frequency is set by an incoming MIDI note.

In MIDI mode, you will see a drop-down menu where you can select an external MIDI source. There
is also a Glide parameter that adjusts the time in milliseconds over which it takes notes to slide their
pitch to the next incoming pitch. You can set a pitch bend range between 0-24 semitones to define the
effect of MIDI pitch bend messages using the PB slider.

26.35.6 Shifter Tips

26.35.6.1 Pitch-shifted Drum Layers

To add glitchy, metallic echoes to a drum loop, duplicate your drum track and add Shifter after the
Drum Rack. In Pitch mode, try adjusting or automating the Coarse knob and enable the Delay button.
Higher pitch shifts will create a metallic and crisp echoed delay. Lower pitch shifts will create a
drawn-out delay effect. You can lower the volume of the pitch-shifted track so that it sits in the
background, adding some movement to the main drum track.

26.35.6.2 Phasing Effects

To create lush phasing effects, minimally adjust (no more than 2 Hz or so) the Fine knob in Freq mode.
Phasing is caused by the interaction of the processed and dry signals; you can adjust the Mix balance
so that both are audible. The strongest phasing will be heard when MIx is at 50%.

26.35.6.3 Tremolo Effects

In Ring mode, frequencies below the audible range (about 20 Hz or slightly lower) create a tremolo
effect. You can also impart a sense of stereo motion to the tremolo by turning on Wide and using small
Spread values.

26.36 Spectral Resonator

The Spectral Resonator Effect.

Based on spectral processing, Spectral Resonator uses spectral resonances and pitched overtones to
add tonal character to any audio source. You can highlight chosen frequencies of the resonating
partials and alter their decay, creating either short percussive reverberations or long washed-out
tones. Choose which frequencies are affected through an internal resonator or via an external MIDI
sidechain. Similar to a vocoder, you can use the MIDI input to place the resonances in key with its

surrounding musical elements, playing the effect polyphonically with up to 16 voices. Spectral
Resonator also offers several spectral processing types on the input signal, including spectral filtering,
spectral chorus, and granularization.

Spectral Resonator uses a spectrogram to display how frequencies in the dry and wet signals behave
over time. Dry signals are represented in yellow, while wet signals are shown in blue. You can hide the
visualization by clicking on its toggle button.

On the left side of the device, you will find the Pitch Mode section. Different controls are available
depending on whether Internal mode or MIDI mode is selected.

When Internal mode is enabled, Spectral Resonator will be tuned to the frequency set by the Freq dial.
The frequency can be set either in Hertz or to a specific pitch; to toggle between the two options, use
the Frequency Dial Mode buttons. Note that the MIDI mode controls are disabled in Internal mode.

When MIDI mode is enabled, Spectral Resonator can be tuned to the frequencies of incoming MIDI
notes. When MIDI mode is enabled, the MIDI router, Mono/Poly switch, Polyphony control, MIDI
Gate, Glide and Pitch Bend range controls are also enabled.

The MIDI router allows you to choose any MIDI track as a source. To use an external MIDI controller,
use the “MIDI From” chooser on any MIDI track to select your MIDI controller. Then, in Spectral
Resonator, choose the track with the selected MIDI controller in the “MIDI From” drop-down chooser.

The MIDI input can be transposed using the Transpose dial (displayed as “Transp. “) with a range of
+/- 48 semitones.

The Mono/Poly switch enables polyphony for incoming MIDI, enabling you to send polyphonic
material such as chords to Spectral Resonator. You can choose between 2, 4, 8, or 16 voices in the
Polyphony chooser. The number of harmonics set by the Harmonics control are evenly distributed
between the voices, resulting in fewer harmonics per voice when high voice counts are used. The
combination of high Polyphony and Unison values will create a darker sound.

When the MIDI Gate button is deactivated, audio input will still excite the resonator, even when no
MIDI notes are playing. When activated, the device behaves more like an instrument, and will only
resonate while MIDI notes are being played. In Polyphonic mode, MIDI Gate is always active, so you
will need to play MIDI notes to produce sound.

The Glide parameter adjusts the time in milliseconds over which it takes notes to slide their pitch to the
next incoming pitch. Note that this is only active in Mono mode. The PB parameter defines the effect of
MIDI pitch bend messages, allowing a range of 0-24 semitones. Note that Spectral Resonator is also
able to receive MPE.

The Harmonics parameter (in the upper right corner of the spectrogram) changes the number of
harmonics. More harmonics will lead to a brighter sound and fewer to a darker sound. Note also that
a higher number of harmonics increases the CPU usage.

Stretch increases or decreases the spacing between the harmonics. Values below 0 will compress the
distance, while values above 0 will stretch it. At 100%, only odd harmonics are created, which leads
to a square-wave type sound.

Shift transposes the input signal’s spectrum up or down within a range of +/- 48 semitones. Note that
this does not shift the spectrum of the actual effect, but rather the spectrum of the signal which is fed to
the effect.

Decay adjusts the decay time in milliseconds. A higher value leads to sustained tones. HF Damp sets
the amount of damping applied to high frequency partials. LF Damp sets the amount of damping
applied to low frequency partials.

For both HF Damp and LF Damp, the frequencies affected by the control shift with the pitch of the Freq
knob (when in Internal mode), or with any incoming MIDI notes (when in MIDI mode).

Using the available switches, you can choose between four Modulations Modes: None, Chorus,
Wander, and Granular. These modes determine how each individual harmonic’s pitch and amplitude
are modulated:

•
•

•
•

None applies no modulation.
Chorus applies triangle wave modulation for every partial. When Mod Rate is set to 0, this
mode only modulates the amplitudes of the partials.
Wander uses random sawtooth waveforms as the modulation source for each partial.
Granular modulates the amplitude of all partials randomly, using exponential decay envelopes.
The partials are generated at random and, in this mode, the Mod Rate parameter affects the
density of the partials.

Both Wander and Granular modes will affect each individual Unison voice, creating very warbly,
dense and indistinct sounds.

All Modulation Modes are also affected by the Mod Rate and Pch. Mod (pitch modulation)
parameters. Mod Rate sets the modulation rate, while Pch. Mod adjusts the range of pitch modulation
in semitones. Though Pch. Mod displays only a positive value, pitch modulation is applied in both a
positive and negative direction (except in Granular mode, where the grain envelopes are only
applied in a positive direction).

The Input Send dial sets the amount of gain applied to the processed signal. There is also a built-in
limiter, to ensure that no signal gets too loud. The LED next to the Input Send dial will light up if the
limiter is in use.

The Unison parameter allows you to choose 1, 2, 4, or 8 voices, while Unison Amount (displayed as
“Uni. Amt”) adjusts the intensity of the unison effect. A higher Unison value increases the number of
voices, and increasing the Unison Amount causes the voices to become further detuned from each
other.

The Dry/Wet adjusts the balance between the processed and dry signals and modifies the visibility of
the two signals in the spectrogram. Set Dry/Wet to 100% when using Spectral Resonator in a return
track.

26.36.1 Spectral Resonator Tips

Here are some tips for using Spectral Resonator:

•

•

•

•

•

Create tonal drum loops by placing Spectral Resonator on a drum track and using the MIDI
sidechain input to feed specific pitches to Spectral Resonator. This can be used to add rhythm to
your track with the same pitches as your bass, for example.
In order to have Spectral Resonator follow the pitches of melodic material, first use the Convert
Harmony to New MIDI Track or the Convert Melody to New MIDI Track command, then send
the generated MIDI track to Spectral Resonator.
Create reverb-type sounds by setting Frequency to a low value, setting Unison and Unison
Amount to a high value, and use the Wander modulation mode in combination with low Mod
Rate and Pch. Mod values. Adjust the Decay parameter to make the “reverb” decay longer or
shorter.
Vocal processing - Spectral Resonator can be used like a vocoder by simply using your voice
as the audio to be processed in combination with the MIDI sidechain input.
Use two Spectral Resonators in series to create overlapping harmonics by sending different
MIDI signals to each of the Spectral Resonators.

26.37 Spectral Time

The Spectral Time Effect.

Spectral Time combines time freezing and spectral delay effects in a single inspiring device. You can
resynthesize your sounds by applying various spectral filters, delays and frequency-shifting techniques
to incoming material, creating highly varied and unique copies. The freeze and delay effects can be
used together or independently, allowing for a wide range of possibilities, such as sustaining any
sound infinitely, or combining delays with time-synced fade transitions. You can easily transform
sounds by smearing frequencies over time, or add metallic echoes and space to any sound source.

Spectral Time has two main sections, Freezer and Delay, which can be used individually or serially,
with the freezer feeding the delay. You can toggle the individual sections using the Freezer On and
Delay On buttons.

Spectral Time uses a spectrogram to display how frequencies in the dry and wet signals behave over
time. Dry signals are represented in yellow, while wet signals are shown in blue. You can hide the
visualization by clicking on its toggle button.

From Spectral Time’s context menu, you can switch Zero Dry Signal Latency on or off. Enabling it
reduces the latency of the dry signal to zero instead of syncing it with the output of the effect. This
option is useful when playing a live instrument through Spectral Time and monitoring the output.

26.37.1 Freezer Section

Spectral Time’s Freezer Section.

Depending on which of the Manual/Retrigger Mode buttons are activated, the Freezer section
controls how the freeze function is triggered and how certain temporal characteristics of the frozen
audio are affected. Note that for both modes, the Freeze button also has to be toggled in order for the
effect to occur.

In Manual mode, audio can be frozen by clicking on the Freeze button. You can also control the Fade
In and Fade Out time of the frozen signal in milliseconds.

In Retrigger mode, you have more controls to fine-tune the rhythm of the frozen audio, which can be
frozen automatically at every transient (onset), or at regular intervals.

Onsets mode will freeze the audio after a transient is detected in the input. Use the Sensitivity knob to
adjust the sensitivity of onset detection. Sensitivity is highest at 100% and lowest at 0%.

Sync mode will freeze the audio at regular intervals, determined by the Interval control. By toggling
the Freezer Time Unit buttons, the Interval control can be set to either milliseconds or beat-time values.

In both Onsets and Sync modes, the Freezer Fade Shape buttons toggle between two available fade
shapes: Crossfade and Envelope. Both fade shapes have different controls to determine how a new
freeze will fade in and out.

When the Crossfade shape is selected, the new freeze will fade in and the old freeze (or dry signal)
will fade out. The crossfade duration is set by the X-Fade control, which specifically determines the
time in milliseconds over which a new freeze will fade in as a percentage of the sync interval set by
the Interval control.

When the Envelope shape is selected, a new freeze will fade in and out according to the millisecond
time values chosen in the Fade In and Fade Out parameters. In this mode, up to eight simultaneous
freezes can be stacked on top of one another.

26.37.2 Delay Section

Spectral Time’s Delay Section.

The Delay section of Spectral Time can be activated or deactivated with the Delay toggle button and
allows you to create delayed copies of spectral information. If the Freezer section is enabled, the
Delay section will be fed by the Freezer’s output.

The Time parameter controls the delay time for the spectral delay lines. The type of value shown here
is dependent on the unit type chosen in the “Mode” drop-down chooser:

•
•
•

Time mode adjusts the delay time in milliseconds.
Notes adjusts delay time in beat divisions.
16th, 16th Triplet, and 16th Dotted set the delay time to the number of the chosen type of 16th
notes.

Feedback sets the amount of output that is fed back to the delay input. Turning this up increases the
audible echoes of the signal.

Shift shifts the frequency of the delayed signals. Each successive delay will be shifted up or down by
the specified frequency amount.

Stereo adjusts the width of the Tilt and Spray controls.

The Dry/Wet control adjusts the balance between the delayed and dry signals. Note that this only
affects the Delay section of the device.

Tilt skews the delay times for different frequencies. A positive value will delay high frequencies more
than low frequencies, while a negative value delays low frequencies more than high frequencies.

Spray distributes the delay times for different frequencies randomly within the given time range.

Mask limits the effects of the Tilt and Spray controls to either high or low frequencies. Positive values
limit the effects to high frequencies, while negative values limit the effects to low frequencies.

26.37.3 Resolution Section

Spectral Time’s Resolution Control.

In the upper right corner of the spectrogram display, you will find the Resolution control, which sets the
resolution used to process the incoming signal. Lower values reduce the overall latency at the cost of
accuracy and fidelity. Note that since higher values affect overall latency, you may wish to reduce the
Resolution while tracking.

26.37.4 Global Controls

Spectral Time’s Global Controls.

Input Send adjusts the gain of the input signal.

The two radio buttons Frz > Dly and Dly > Frz reverse the effect order.

The global Dry/Wet control adjusts the balance between the processed and dry signals. Set it to
100% when using Spectral Time in a return track.

26.38 Spectrum

The Spectrum Device.

Spectrum performs real-time frequency analysis of incoming audio signals. The results are represented
in a graph, with dB along the vertical axis and frequency/pitch along the horizontal. The peak levels
are retained on the graph until the song is restarted. Note that Spectrum is not an audio effect, but
rather a measurement tool — it does not alter the incoming signal in any way.

The Block chooser selects the number of samples that will be analyzed in each measurement. Higher
values result in better accuracy, but at the expense of increased CPU load.

Channel determines which channel is analyzed — left, right or both.

The Refresh slider determines how often Spectrum should perform an analysis. As with the Block
parameter, this allows for a tradeoff between accuracy and CPU load. A fast response time is more
accurate, but also more CPU intensive.

The Avg slider allows you to specify how many blocks of samples will be averaged for each update
of the display. With a setting of one, each block is shown. This results in much more activity in the
display, which can be useful for finding the spectrum of short peaks. As you increase the Avg value,
the display updates more smoothly, providing an average of the spectrum over time. This is more
consistent with the way we actually hear.

The Graph button switches between displaying the spectrum as a single interpolated line and discrete
frequency bins.

Max toggles the display of the accumulated maximum amplitude. With Max enabled, you can reset
the maximum amplitude by clicking in the display.

The Scale X buttons allow you to toggle the scaling of the frequency display between linear,
logarithmic, and semitone. Note that logarithmic and semitone are actually the same scaling, but

switch the legending at the top of the display between Hertz and note names. Linear scaling is
particularly useful for detailed analysis of high frequencies.

As you move your mouse over Spectrum’s display, a box appears that shows the amplitude,
frequency and note name at the pointer’s position. The Range/Auto button at the bottom left of
Spectrum’s interface toggles between manually and automatically adjusting the display’s dynamic
range. With Range selected, you can zoom and scroll the amplitude by moving your mouse over the
amplitude legending on the display’s left side. Drag vertically to scroll and horizontally to zoom. You
can also use the Range sliders to set the minimum and maximum amplitude values shown. With Auto
selected, the display automatically scales itself based on the incoming audio level. Note that in Auto
mode, the Range sliders and zooming are disabled.

To get an even better view, you can toggle the location of the display between the device chain and
Live’s main window by clicking the
display.

 button in Spectrum’s title bar or by double-clicking in the

26.39 Tuner

The Tuner Device.

Tuner analyzes and displays the incoming monophonic pitch as well as its distance from the nearest
semitone. Based on classic guitar tuners, Tuner’s large display is designed for easy visibility on stage,
and is perfect for tuning external instruments or synthesizers.

It is important to note that Tuner is not an audio effect, but rather a measurement tool – it does not
alter the incoming signal in any way. Tuner is designed to analyze monophonic pitches, and works

best with a clean, clear signal. Polyphonic, noisy, or harmonically rich signals may yield inaccurate
results.

26.39.1 View Switches

The two buttons in the lower-left switch between Tuner’s two main views. Classic View resembles
conventional analog tuners while Histogram View shows pitch over time. In both views, the display
uses color to help indicate tuning accuracy. Green means in tune, while red means out of tune.

Tuner’s View Switches.

26.39.2 Classic View

In Classic View, the incoming pitch is represented as a colored ball along a curve, and the nearest
detected note name is shown in the center of the display. The arrows on either side of the note name
light up to indicate whether the signal needs to be tuned higher or lower in order to reach the desired
pitch.

In Target Mode, a circular outline in the center of the curve shows the desired pitch, and your signal is
in tune if the colored ball is exactly within this outline. If the incoming signal is sharp, the ball will
appear to the right of the target, while flat signals will appear to the left.

Tuner in Target Mode.

In Strobe Mode, the curve becomes a rotating band of lights. The direction of rotation indicates
whether the signal is sharp or flat. If the band rotates to the right, the incoming pitch is sharp, while flat
signals cause the band to rotate to the left. The further your signal is out of tune, the faster the band will
move.

Tuner in Strobe Mode.

The Hertz/Cents Switch toggles between showing the absolute frequency of the incoming signal in
Hertz or the distance from the target pitch in cents. This switch is also visible in the Histogram View.

26.39.3 Histogram View

In Histogram View, pitch is shown over time. The scale on the right of the display shows the possible
note names, and the horizontal gray bars represent the perfectly in-tune “center” of the associated
note. Sharp notes will appear above their corresponding gray line, while flat notes will appear below
it.

Tuner in Histogram View.

Drag up or down in the display to scroll to different pitches, or drag horizontally to zoom in or out.
With Auto enabled, the display will automatically adjust so that the incoming pitch is in the center of
the display.

The Hertz/Cents Switch toggles between showing the absolute frequency of the incoming signal in
Hertz or the distance from the target pitch in cents. This switch is also visible in the Classic View.

26.39.4 Note Spellings

Tuner’s Note Spellings.

The Tuner device includes three options for note spellings. You can access a menu with these options
when you right-click anywhere within Tuner’s view display:

•
•
•

Sharps (C#)
Flats (D♭)
Sharps and Flats (C#/D♭)

26.39.5 Reference Slider

Tuner’s Reference Slider.

The Reference slider allows you to change the tuning reference that Tuner uses when analyzing
incoming signals. By default this is set to 440 Hz, which is “standard” concert tuning, but it can be
changed to any value between 410-480 Hz.

26.40 Utility

The Utility Effect.

Utility can perform some very useful tasks, especially in combination with other devices.

There are two separate Phase controls, one for each input channel (Left and Right). As their names
imply, they invert the phase of each channel.

The Channel Mode chooser allows selective processing of the left and right channels of a sample. If,
for example, Left is selected, the right channel is ignored and the left channel appears on both
outputs. This is especially useful if you have a stereo file that contains different information on both
channels and you want to use only one.

The Width control sets the stereo width of the wet signal. 0% yields a mono signal whereas values
above 100% create a widened stereo panorama.

Choosing Mid/Side Mode from the Width control’s context menu allows you to you toggle between
the Width and Mid/Side controls. The Mid/Side control acts as a continuous mono to stereo
controller when set from 0 to 100M. Setting the parameter to 100M will sum the audio to mono.
Values between 0 and 100S emphasize the stereo or “out of phase” components of a signal. At
100S, only the side signal will be heard. The left and right channels will be 180 degrees out of phase
with each other.

Note that if either Left or Right have been chosen in the Channel Mode chooser, the Width and Mid/
Side controls have no function, and are therefore disabled.

When the Mono switch is enabled, the stereo input signal is converted to mono.

The Bass Mono switch converts the low frequencies of the input signal to mono. This is useful for
avoiding coloration of low frequencies when they are replayed in mono. You can use the Bass Mono
Frequency slider to adjust the cutoff frequency between 50-500 Hz.

When Bass Mono Audition is enabled, only the low frequencies can be heard. This can be useful for
tuning the Bass Mono Frequency.

The Gain control adjusts the level of the input signal from -infinite dB to +35 dB. This can be
particularly useful for automating volume fades on a track, while freeing up that track’s Volume control
for mix balancing. When adjusting the Gain parameter between -18 and +35 dB using the up and
down arrow keys, the value increases or decreases in 1 dB increments. However, between -18 dB
and -inf dB, the value smoothly accelerates.

The Balance control pans the signal anywhere in the stereo field.

The Mute button simply silences the incoming signal when enabled. The active/mute controls of a
track are always placed at the very end of the signal chain. However, since you can place Utility
anywhere in a signal chain, you can use its mute function to cut the input of a delay line or reverb
without turning off the output of these devices.

The DC switch filters out DC offsets and extremely low frequencies that are far below the audible
range. It will only have a sonic effect if a signal contains these frequencies and is processed after
Utility with nonlinear effects such as compressors or waveshapers.

26.41 Vinyl Distortion

The Vinyl Distortion Effect.

The Vinyl Distortion effect emulates some of the typical distortions that occur on vinyl records during
playback. These distortions are caused by the geometric relationships between the needle and the
recorded groove. The effect also features a crackle generator for adding noisy artifacts.

The Tracing Model section adds even harmonic distortion to the input signal. Adjust the amount of
distortion with the Drive knob, or click and drag vertically in the Tracing Model X-Y display. To adjust
the distortion’s frequency or ”color,” drag horizontally in the X-Y display or double-click on the Freq
field and type in a value. Holding the Alt (Win) / Option (Mac) modifier while dragging
vertically in the X-Y display changes the frequency band’s Q (bandwidth).

The Pinch Effect section adds odd harmonics to the input signal. These distortions typically occur 180
degrees out of phase, creating a richer stereo image. The Pinch Effect has the same controls as the
Tracing Model, but generates a rather different sound.

The Drive control increases or decreases the overall distortion amount created by both the Tracing
Model and Pinch.

There are two distortion modes: Soft and Hard. The Soft Mode simulates the sound of a dub plate,
while Hard Mode is more like that of a standard vinyl record.

The stereo/mono switch determines whether the Pinch distortion occurs in stereo or mono. Set it to
stereo for realistic simulation of vinyl distortions.

The Crackle section adds noise to the signal, with noise density set by the Density control. The Volume
control adjusts the amount of gain applied to the noise.

26.42 Vocoder

The Vocoder Effect.

(Note: The Vocoder effect is not available in the Intro and Lite Editions.)

A vocoder is an effect that combines the frequency information of one audio signal (called the carrier)
with the amplitude contour of another audio signal (called the modulator). The modulator source is
generally something with a clear rhythmic character such as speech or drums, while the carrier is
typically a harmonically-rich synthesizer sound such as a string or pad. The most familiar application
of a vocoder is to create ”talking synthesizer” or robotic voice effects.

Vocoders work by running both the carrier and modulator signals through banks of band-pass filters.
The output level of each of the modulator’s filters is then analyzed and used to control the volume of
the corresponding filter for the carrier signal.

Live’s Vocoder should be inserted on the track that contains the audio material you plan to use as your
modulator. The Carrier chooser then provides a variety of options for the carrier signal:

•

•

•

Noise uses Vocoder’s internal noise generator as the carrier source. With this selected, an X-Y
display is shown which allows you to adjust the character of the noise. The horizontal axis
adjusts downsampling. Click and drag to the left to decrease the sample rate of the carrier’s
output. The vertical axis adjusts the density of the noise. Click and drag downward to decrease
the density.
External allows you to select any available internal routing points from the choosers below. This
is the option you’ll want for classic ”robot voice” applications.
Modulator uses the modulator itself as the carrier. This essentially outputs a resynthesized
version of the modulator signal, but allows you to use Vocoder’s sound-shaping controls to
adjust the sound.

•

Pitch Tracking enables a monophonic oscillator, which tunes itself to the pitch of the modulator.
The High and Low sliders allow you to limit the frequency range that the oscillator will attempt
to track. Choose from sawtooth or one of three pulse waveforms and adjust the coarse tuning of
the oscillator via the Pitch slider. Pitch tracking is particularly effective with monophonic
modulator sources such as melodic instruments or voices. Note that the oscillator only updates
its frequency when it detects a clear pitch. It then maintains this pitch until it detects a new one.
This means that changing the oscillator’s parameters or causing it to reset (when grouping
Vocoder’s track, for example) can cause unexpected changes in the sound. With polyphonic
material or drums, pitch tracking is generally unpredictable (but can be very interesting.)

Particularly when using external carrier sources, a vocoder’s output can sometimes lose a lot of high
end. Enabling the Enhance button results in a brighter sound by normalizing the spectrum and
dynamics of the carrier.

The Unvoiced knob adjusts the volume of an additional noise generator, which is used to resynthesize
portions of the modulator signal that are pitchless, such as ”f” and ”s” sounds.

Sens. sets the sensitivity of the unvoiced detection algorithm. At 100%, the unvoiced noise generator is
always on. At 0%, only the main carrier source is used. The Fast/Slow switch adjusts how quickly
Vocoder switches between unvoiced and voiced detection.

Vocoder’s large central area shows the levels of the individual band-pass filters. Clicking within this
display allows you to attenuate these levels.

The Bands chooser sets the number of filters that will be used. Using more bands results in a more
accurate analysis of the modulator’s frequency content, but requires more CPU.

The Range sliders adjust the frequency range over which the band-pass filters will operate. For most
sources, a fairly large range works well, but you may want to adjust the outer limits if the sound
becomes too piercing or bassy. The BW control sets the bandwidth of the filters. At low percentages,
each filter approaches a single frequency. As you increase the bandwidth, you increase the overlap
of the filter bands. A bandwidth of 100% is the most accurate, but higher or lower settings can create
interesting effects.

The Precise/Retro switch toggles between two types of filter behavior. In Precise mode, all filters have
the same gain and bandwidth. In Retro mode, bands become narrower and louder at higher
frequencies.

Gate sets a threshold for the filterbank. Any bands whose levels are below the threshold will be silent.

The Level slider boosts or cuts Vocoder’s output.

Depth sets how much of the modulator’s amplitude envelope is applied to the carrier’s signal. At 0%,
the modulator’s envelope is discarded. At 200%, only high amplitude peaks will be used. 100%
results in ”classic” vocoding.

The Attack and Release controls set how quickly Vocoder responds to amplitude changes in the
modulator signal. Very fast times preserve the transients of the modulator, but can cause distortion
artifacts.

The Mono/Stereo switches determine how many channels are used for the carrier and modulator. In
Mono mode, both the carrier and modulator are treated as mono sources. Stereo uses a mono
modulator but processes the carrier in stereo. L/R processes both the carrier and modulator signals in
stereo.

The frequencies of the carrier’s filterbank can be shifted up or down via the Formant knob. With voice
as the modulator, small Formant changes can alter the apparent gender of the source.

The Dry/Wet control adjusts the balance between the processed and dry signals.

26.42.1 Vocoder Tips

This section explains how to set up the most common Vocoder applications.

26.42.1.1 Singing Synthesizer

The classic vocoder application is the ”singing synthesizer.” To set this up in Live:

1.

2.

3.
4.

5.

6.

Insert Vocoder in the track that contains your vocal material. You can either use a clip that
contains a prerecorded voice clip or, to process a live vocal signal, connect a microphone to a
channel on your audio hardware and choose this as the input source for the track.
Insert a synthesizer such as Analog in another track. Again, you can either create a MIDI clip to
drive this synthesizer or play it live.
Set the vocoder’s Carrier chooser to External.
Select the synthesizer track in the vocoder’s Audio From choosers. (For best results, choose Post
FX in the bottom chooser.)
If you’re creating your synthesizer and vocal material in real time, make sure the Arm button is
enabled on both tracks.
Play the synthesizer as you speak into the microphone. You’ll hear the rhythm of your speech,
but with the timbral character and frequencies of the synthesizer. To hear the vocoded signal
alone, solo the voice track so that the ”normal” synthesizer track is muted.

Note: you’ll generally get the best results if your synthesizer sound is bright and rich in harmonics. Try
sawtooth-based patches to improve the intelligibility of the voice. For even more brightness and
clarity, try adjusting the Unvoiced control and/or enabling Enhance.

26.42.1.2 Formant Shifter

If the Vocoder is set to use the modulator as its own carrier, it can be used as a powerful formant
shifter. To do this:

1.
2.
3.

Set the Carrier chooser to Modulator.
Set the Depth to 100%.
Enable Enhance.

Now experiment with different settings of the Formant knob to alter the character of the source. For
even more sound-sculpting possibilities, try adjusting the various filterbank parameters as well.

27. Live MIDI Effect Reference

Live comes with a selection of custom-designed, built-in MIDI effects. These effects can modify
incoming MIDI pitch, length, and velocity data in various ways. You can use a MIDI effect on its own
to add variation to a pattern or combine multiple MIDI effects to create more complex note
sequences.

All MIDI effects with pitch controls support scale awareness. When the Use Current Scale toggle in the
device title bar is enabled, any pitch-related controls can be adjusted in scale degrees instead of
semitones. This ensures that all note transpositions stay within a specific harmonic range.

To learn the basics of using effects in Live, check out the Working with Instruments and Effects chapter.

27.1 Arpeggiator

The Arpeggiator Effect.

Arpeggiator creates rhythmical patterns using the notes of a chord or a single note. It offers a
complete set of both standard and unique arpeggiator features.

Arpeggiators are a classic element in 80s synth music. The name originates from the musical concept
of the arpeggio, in which the notes comprising a chord are played as a series rather than in unison.
“Arpeggio” is derived from the Italian word “arpeggiare,” which refers to playing notes on a harp.

The Style chooser determines the sequence of notes in the rhythmical pattern. When a style is selected,
a visualization of the pattern is shown in the display. You can use the Previous Style Pattern and Next
Style Pattern buttons in the display to cycle through patterns.

Most style patterns are common to standard arpeggiators, such as Up, Down, Converge, and
Diverge. There are also a couple of unique patterns:

•

•

Play Order arranges notes in the pattern according to the order in which they are played. This
pattern is therefore only recognizable when more than one chord or note has been played.
Chord Trigger repeats the incoming notes as a block chord.

Additionally, there are three patterns for random arpeggios:

•
•

•

Random generates a continuously randomized sequence of incoming MIDI notes.
Random Other generates random patterns from incoming MIDI notes, but will not repeat a
given note until all other incoming notes have been used.
Random Once generates one random pattern from incoming MIDI notes and repeats that
pattern until the incoming MIDI changes, at which point a new pattern is created.

The arpeggiated pattern plays at the speed set by the Rate control, which uses either milliseconds or
tempo-synced beat divisions, depending on which Sync/Free Rate toggle is selected.

You can transpose the pattern using the Distance and Steps controls. The Distance control sets the
transposition in semitones or scale degrees, while the Steps control determines how many times the
pattern is transposed. The pattern initially plays at its original pitch and then repeats at progressively
higher transpositions when using positive Distance values or lower transpositions when using negative
values. For example, when Distance is set to +12 st and Steps is set to 2, a pattern starting with C3 will
play first at C3, then C4, and finally at C5.

To transpose the pattern within a specified scale, use the Root and Scale choosers to select your
desired settings. You can also transpose the pattern based on the clip’s scale by enabling the Use
Current Scale toggle in the device title bar. When this option is enabled, the Root and Scale choosers
are deactivated as these settings are determined by the clip.

The Gate control determines the length of the notes in the pattern as a percentage of the Rate value.
Gate values above 100% result in notes that overlap, creating a legato effect.

When playing notes using a MIDI controller, you can enable the Hold switch to keep the pattern
playing even after releasing the keys. The pattern will continue to repeat until another key is pressed.
You can hold an initial set of keys and then press additional keys to add notes to a currently held
pattern. To remove notes, play them a second time. This allows you to create a gradual buildup and
rearrangement of the pattern over time.

The Pattern Offset control shifts the sequence of notes in the pattern by a specified number of steps.
Imagine the pattern as a circle of notes that is played in a clockwise direction from a set start point —
Pattern Offset effectively rotates this circle counterclockwise one note at a time, shifting the starting
note. For example, if the offset is set to 1, the second note in the pattern plays first and the original first
note plays last.

You can add swing to the pattern by selecting a groove from the Groove chooser. Grooves in
Arpeggiator function similarly to grooves in clips. The intensity of the groove is determined by the
Global Groove Amount slider in the Groove Pool or the Control Bar.

The pattern can be restarted at specific intervals depending on the selected Retrigger option:

•
•
•

Off — The pattern is never retriggered.
Note — The pattern is retriggered when a new note is played.
Beat — The pattern is retriggered on a specified bar or beat, as set by the Interval control.

The LED next to the Retrigger controls flashes each time the pattern is retriggered.

The Repeats control specifies how many times the pattern is repeated. By default, Repeats is set to ∞
so that the pattern plays indefinitely. Setting Repeats to 1 or 2 can emulate the strumming of a guitar,
for example. You can also combine different Repeats values with various Retrigger settings to create
rhythmically generated arpeggios with pauses in between.

You can enable the Velocity toggle to access the velocity controls for the pattern. Decay sets the time
required to reach the velocity value specified by the Target control. For example, using a long Decay
time and setting Target to 0 produces a gradual fade-out.

When the Retrigger switch is enabled, the velocity slope is retriggered each time the pattern is
retriggered. Combining velocity and Beat retriggering adds rhythmic variation to the pattern’s velocity
slope.

27.2 CC Control

The CC Control Effect.

CC Control lets you send MIDI CC messages to hardware devices. It features three fixed control
knobs (Mod Wheel, Pitch Bend, Pressure), one customizable button for sending on/off or minimum/
maximum values (Custom A), and twelve customizable control dials (Custom B - M).

The device’s fixed control knobs function as follows:

Mod Wheel – Sets the amount of modulation being applied by the receiving device.

Pitch Bend – Sends out pitch bend data to the receiving device. Negative values adjust the range
downward and positive values adjust the range upward.

Pressure – Sets the amount of channel pressure/aftertouch being applied by the receiving device.

The Custom A button sends out on/off or minimum/maximum values, which can be toggled between
by turning the button on or off. While intended for sending sustain/hold pedal messages (CC 64), this
button can be assigned to any other MIDI parameter via its CC Type Chooser drop-down menu.

The Custom B - M controls can be renamed and assigned to any MIDI parameter via each control’s
CC Type Chooser drop-down menu. Custom names and assignments for these controls are shown on
Push and are saveable as presets, allowing for easy navigation and reuse. Parameter values can be
set using automation lanes or modulated in real time via the device’s control dials, which can be useful
both for structuring and improvising with performances.

In the device’s title bar, there are two toggles for switching between controls 1 - 8 and controls 9 - 16,
as well as a Send button that sends out all current MIDI CC values when clicked. Enabling the Learn

toggle allows you to send CC data from an incoming MIDI source to any customizable control. This
provides a quick way of personalizing the device. Using Learn also makes it easy to identify which
CC message an external controller is sending.

Note that if CC automation already exists for any CC message being sent from CC Control to a
receiving device, MIDI data between the two is merged.

27.3 Chord

The Chord Effect.

As the name suggests, this effect creates a chord using the pitch of each incoming note along with up
to six additional pitches.

You can use the Shift 1-6 controls to assign which pitches are used to contribute to a chord from a
range of ±36 semitones relative to the original note. For example, setting Shift 1 to +4 semitones and
Shift 2 to +7 semitones yields a major chord in which the incoming note is the root. Pitches can be set
in any order — it makes no difference which Shift control is used for which pitch. The LED next to each
Shift knob flashes to indicate when its corresponding note is being played.

Note that the same pitch cannot be assigned to multiple Shift controls. For example, you cannot set
both Shift 2 and Shift 3 to +8 st. If a pitch is already assigned to a Shift control, any additional
assignments of the same pitch will be deactivated.

In addition to setting pitches manually, you can enable the Learn toggle in the device title bar to
assign pitches by playing a chord on an external MIDI controller. To do so, hold the keys you want to

include in the chord. The pitch of the first held key determines the root and is not assigned to a Shift
control; any subsequent pitches are assigned to the Shift controls in order. You can add more pitches
by holding new keys while keeping the original keys held. Once the desired pitches are assigned,
deactivate the Learn toggle.

When the Velocity or Chance toggle is enabled, you can adjust the dynamics of the generated note
using the slider underneath each Shift control:

•

•

Velocity sets the velocity for a generated note. This is a relative control, with a range of 1% to
200%. At 100%, the velocity of the generated note matches the velocity of the incoming note.
Varying the velocities between notes can introduce subtle overtones or dramatically alter a
chord’s balance.
Chance sets the probability that a generated note will play when an incoming note is triggered.
You can set the probability anywhere from 0% to 100%. At 100%, a note is generated for
every incoming note.

Using both Velocity and Chance together is a good way to add dynamic variations to a generated
chord.

You can use the Strum control to add a delay of up to 400 ms between the notes of a generated
chord. At positive values, the strumming starts with the original note, followed by the notes from Shift 1
to Shift 6. At negative values, this order is reversed. You can add duplicate notes by enabling the Play
Duplicate Notes When Strumming option in the device title bar’s context menu.

There are two additional controls that can be used to further shape the strumming:

•

•

Tension adjusts the speed of the strumming. At positive values, the strumming starts slowly and
accelerates with each additional note, while at negative values, it starts quickly and gradually
slows down.
Crescendo applies a velocity ramp to the strummed notes. Positive values create an upward
ramp, and negative values create a downward ramp.

By default, pitches are set in semitones; however, you can enable the Use Current Scale toggle in the
device title bar to set pitches in scale degrees.

You can enable the Send Per Note Events to Generated Notes option in the device title bar’s context
menu to send out MPE data to the notes in a generated chord. When scale awareness is also
enabled, per-note pitch bend messages follow the clip’s scale so that bent chords stay within the
expected harmonic range.

27.4 Note Length

The Note Length Effect.

Note Length alters the length of incoming MIDI notes. It can also be used to trigger notes from MIDI
Note Off messages, instead of the usual Note On messages.

The Trigger Source toggle determines whether the device is triggered by Note On or Note Off
messages. When set to Note On, the length of incoming notes is determined by the Gate and Length
controls. The Gate control defines how the value set by the Length control is applied. At 100%, notes
play for the total duration specified by the Length control. Setting Gate to 200% doubles the length,
while setting it to 50% halves the length. You can use the Time Mode toggles to adjust the length in
milliseconds or tempo-synced beat divisions.

When the device is set to trigger from a Note Off event (the moment a note is released), the timing of
an incoming note is delayed by its length — meaning the note starts at the moment it would have
stopped if triggered by a Note On message. Once the initial delay is reached, the timing specified by
the Gate and Length controls is applied.

Three additional parameters are available when using Note Off messages:

•

•

Release Velocity — Determines the velocity of the output note. The percentage sets the balance
between the incoming note’s Note On and Note Off velocities. If your keyboard does not
support MIDI Note Off velocity, you can leave this set to 0%.
Decay Time — Sets the time needed for an incoming note’s velocity to decay to zero. The
decay begins immediately from the moment the device receives a Note On message. The value
at the time of Note Off becomes the velocity of the output note.

•

Key Scale — Alters the length of output notes based on the pitch of incoming notes. At positive
values, notes below C3 are made progressively longer, while notes above C3 are made
shorter. Negative values invert this behavior.

You can enable the Latch toggle to activate note latching. When using Note On messages, triggered
notes continue playing until the next Note On message is received. When using Note Off messages,
notes are triggered once all keys (or a sustain pedal, if connected) are released and a new Note Off
message is received. In both cases, the Gate and Length controls are deactivated, as the length of
triggered notes depends on the Note On/Off messages. Additionally, the Release Velocity, Decay
Time, and Key Scale controls are deactivated for Note Off messages.

27.5 Pitch

The Pitch Effect.

Pitch transposes incoming MIDI notes by ±128 semitones or ±30 scale degrees.

You can use the Pitch control to set the transposition for incoming pitches. By default, notes are
transposed in semitones. Enable the Use Current Scale toggle in the device’s title bar to transpose
notes by scale degrees.

The Step Up and Step Down buttons let you increase or decrease the Pitch control value by the
distance set by the Step Width slider. The Step Width distance can range from 1 to 48 semitones or 1
to 30 scale degrees when Use Current Scale is enabled. All of these controls can be assigned Key
and/or MIDI mappings for real-time adjustment.

The Lowest and Range controls define the pitch range through which notes are allowed to pass
through the effect.

You can select an option in the Mode chooser to determine how notes outside the set range are
processed:

•

•
•

In Block mode, notes outside the range are blocked from passing through. The LED next to the
Range control flashes when this happens.
In Fold mode, notes outside the range are transposed to fit within the range.
In Limit mode, notes are restricted to the range. This means that any notes below the lowest note
in the range are transposed up to that note, and any notes above the highest note in the range
are transposed down to fit.

27.6 Random

The Random Effect.

Random adds an element of unpredictability to note sequences by randomizing the pitch of incoming
notes.

The Chance control determines how likely it is that an incoming note’s pitch will be randomly altered.
You can think of it as a dry/wet control for randomness.

The random value that determines the pitch change is created by two variables: the Choices and
Interval controls. The Choices control defines the number of possible pitches, ranging from 1 to 24. The

Interval control defines the number of possible intervals between the pitches. The values of these two
controls are multiplied to determine the total range of possible pitches relative to the incoming note.

For example, when Chance is set to 50%, Choices is set to 1, and Interval is set to 12, repeatedly
playing C3 results in half of the notes playing at C3 and half at C4, in no particular order. If you swap
the Choices and Interval values by setting Choices to 12 and Interval to 1, half of the notes will play at
C3, while the other half will play at any note between C#3 and C4. These examples assume that
Mode is set to Random and Sign is set to Add, which are the default settings.

Mode determines how the randomization occurs: Random assigns pitches in no particular order, while
Alt cycles through pitches in a fixed round-robin order. The Chance control behaves differently in this
mode: at 100%, the next output note will always be the next note in the sequence, while at 0%, the
next output note will always be the incoming note.

For example, when Chance is set to 100%, Choices is set to 12, and Interval is set to 1, playing C3
once plays C3, and each successive C3 plays the next semitone higher until C4, at which point the
cycle starts over from C3. When Chance is set to 100% and Choices and Interval are set to 2,
incoming C3s alternate between C3 and D3. This behavior is ideal for simulating upbow and
downbow alternation with stringed instruments, or alternating right- and left-hand drum samples.

Sign determines how random pitches are generated relative to the incoming note:

•
•
•

Add generates random pitches that are higher than the original note.
Sub generates random pitches that are lower than the original note.
Bi generates random pitches that can be both higher and lower than the original note.

The LEDs to the right of the Chance control indicate how random pitches are assigned:

•
•
•

The + LED flashes when a pitch above the original note is generated.
The 0 LED flashes when the pitch remains unchanged.
The - LED flashes when a pitch below the original note is generated.

You can enable the Use Current Scale toggle in the device title bar to constrain randomly generated
pitches to the clip’s scale. This ensures that the output values stay within a specific harmonic range.
When using Random’s Alt mode with a defined scale, you can create the effect of a simple yet
unpredictable step sequencer.

27.7 Scale

The Scale Effect.

Scale remaps notes based on a defined scale. Each incoming note is assigned an outgoing
equivalent in a matrix. This means you can convert all incoming Cs to Ds, for example.

The Note Matrix uses a 13x13 grid where each row and column corresponds to the 12 notes in an
octave. The X-axis shows the incoming note values, while the Y-axis shows their outgoing equivalents.

The black squares correspond to the black keys on a keyboard. The highlighted squares determine
how each note is mapped based on the set scale. The scale mapping begins from the root note,
located in the bottom left corner of the Note Matrix. You can set the root note using the Base chooser
and select a scale using the Scale Name chooser. Alternatively, you can enable the Use Current
Scale toggle in the device title bar to apply the clip’s root note and scale. Once enabled, the Base
and Scale Name choosers are deactivated, as the clip defines these settings.

You can create your own scale by selecting User from the Scale Name chooser. By default, each
highlighted square is mapped to its corresponding note within an octave — C outputs C, C# outputs
C#, and so on. You can move highlighted squares with the mouse or delete them with mouse clicks to
customize which notes are included in the scale. Removing a note from the Note Matrix means that
note will no longer be output, even if played.

Use the Transpose slider to raise or lower the pitch of incoming MIDI notes by ±36 semitones. You
could, for example, shift a melody written in C major to G major by setting Transpose to +7 st.

When the Scale Name is set to User, you can enable the Fold switch to automatically fold notes if their
distance from the original note is greater than six semitones. For example, if an incoming C3 is
mapped to an outgoing A3, enabling Fold means that C3 will map to A2 instead.

The Lowest and Range controls define the note range for the scale mapping. By default, all octaves
are included, but you can limit the range to creatively remap some notes while leaving the rest
unaffected. For example, if Lowest is set to C2 and Range is set to +36, only the notes C2 through B4
will be remapped when using a C major scale. These controls can be used in conjunction with the
Transpose parameter to apply transposition only to a specific range of notes. You can, using the same
settings from the example, set the Transpose control to +7 st so that only the notes between C2 and B4
are transposed, while the others remain unaffected.

27.8 Velocity

The Velocity Effect.

Velocity alters the velocity values (1-127) of incoming MIDI notes to ensure their outgoing values stay
within a specified range.

The Velocity Curve grid shows how the incoming velocities that fall within the range set by the Range
and Lowest controls (X-axis) are remapped based on the range set by the Out Hi and Out Low
controls (Y-axis). The resulting curve defines how the velocity values are altered.

You can, for example, set Out Low to 80 and Out High to 127 to constrain all outgoing velocities to a
higher range, even if the original notes were played softly. Note that if Lowest and Out Low are set to

zero, and Range and Out Hi are set to 127, the effect is essentially bypassed, as all incoming velocity
values will output within a similar range.

Velocity values can be remapped for MIDI Note On (Velocity) or Note Off (Rel. Vel.) messages, or
both, depending on the option set via the Operation chooser.

You can choose how incoming velocities that are outside the range set with the Range and Lowest
controls are processed using one of the Mode toggles:

•
•

•

In Clip mode, incoming velocities are clipped so that they stay within the range.
In Gate mode, incoming velocities outside the range are removed altogether. When a note is
blocked by the gate, the LED below the Velocity Curve grid flashes.
In Fixed mode, the Out Hi value defines all outgoing velocity values, regardless of the incoming
velocities.

Random introduces random modulation to all incoming velocities. The range of modulation is
determined by the set value and is influenced by the Output Range controls. For example, when Out
Hi is set to 127 and Out Low is set to 60, a Random value of 50 shifts the velocities up or down by up
to 50 within the range of 60-127.

When using positive Random values, a gray-shaded area appears around the velocity curve to
indicate that the velocities are subject to the set random range.

The Drive and Compand controls can be used to create a more complex velocity curve. Drive pushes
all values in the curve to the outer extremes; Compand can either expand or compress the values
within the boundaries of the curve.

Positive Drive values shift the velocities to the upper part of the range so that most notes play loudly,
while negative values shift the velocities to the lower part of the range so that most notes play softly.

Positive Compand values expand incoming velocities to the outer boundary of the curve, shifting the
outgoing values toward the higher or lower extremes. Negative Compand values compress outgoing
velocities toward the mid-range.

You can use these two controls separately or together to further sculpt the velocity curve, creating a
more defined result within the general range.

28. Live Instrument Reference

Live comes with a selection of custom-designed, built-in instruments, including devices based on
physical modeling, FM synthesis, and wavetable synthesis, among others.

To learn the basics of using instruments in Live, check out the Working with Instruments and Effects
chapter.

Note that different editions of Live have different feature sets, so some instruments covered in this
reference may not be available in all editions.

28.1 Analog

The Analog Instrument.

Analog is a virtual analog synthesizer, created in collaboration with Applied Acoustics Systems. With
this instrument, we have not attempted to emulate a specific vintage analog synthesizer but rather to
combine different features of legendary vintage synthesizers into a modern instrument. Analog
generates sound by simulating the different components of the synthesizer through physical modeling.
This technology uses the laws of physics to reproduce how an object or system produces sound. In the
case of Analog, mathematical equations describing how analog circuits function are solved in real
time. Analog uses no sampling or wavetables; the sound is simply calculated in real time by the CPU
according to the values of each parameter. This sound synthesis method ensures unmatched sound
quality, realism, warmth and playing dynamics.

28.1.1 Architecture and Interface

Analog’s signal flow is shown in the figure below:

Diagram of Analog’s Signal Flow.

The primary sound sources of the synthesizer are two oscillators and a noise generator. These sources
can be independently routed to two different multi-mode filters, which are each connected to an
amplifier. Furthermore, the signal flow can be run through the filters in series or in parallel.

Analog also features two low-frequency oscillators (LFOs) which can modulate the oscillators, filters
and amplifiers. Additionally, each filter and amplifier has its own envelope generator.

The Analog interface consists of two parts: the display surrounded on all sides by the shell. The shell
contains the most important controls for a given section while the display updates to show parameter
visualizations and additional controls for the section selected in the shell. In addition to the synthesis
modules, there is a Global section that contains general performance parameters such as instrument
volume, vibrato and polyphony, as well as an MPE section that includes controls for three MPE
sources: pressure, slide and per-note pitch bend, which make it possible to shape Analog’s sound
using an MPE-enabled controller.

28.1.2 Oscillators

Display and Shell Parameters for the two Oscillators.

Analog’s two oscillators use physical modelling to capture the character of vintage hardware
oscillators. Because they use modelling instead of wavetables, they avoid aliasing.

Each oscillator can be turned on or off independently via the switch labelled Osc 1 or Osc 2 in the
shell, and the oscillator’s output level is adjusted by the slider to the right of this activator.

The F1/F2 slider controls the balance of the oscillator’s output to each of the two filters. When the
slider is at the center position, equal amounts of signal will be sent to both filters. When set all the way
to the top or bottom, signal will only be sent to Filter 1 or Filter 2 respectively.

The Shape chooser selects the oscillator’s waveform. The choices are sine, sawtooth, rectangular and
white noise. When rectangular is selected, the Pulse Width parameter is enabled in the display, which
allows you to change the pulse width of the waveform. Low Width values result in a very narrow
waveform, which tends to sound tinny or “pinched.“ At 100%, the waveform is a perfect square,
resulting in only odd harmonics. The pulse width can also be modulated by an LFO, via the slider next
to Width. Note that this parameter is only enabled when the corresponding LFO is enabled.

The Octave, Semi and Detune knobs in the shell function as coarse and fine tuners. Octave transposes
the oscillator by octaves, while Semi transposes up or down in semitone increments. The Detune knob
adjusts in increments of one cent (up to a maximum of three semitones (300 cents) up or down).

Oscillator pitch can be modulated according to the settings of the Pitch Mod and Pitch Env
parameters in the display. The LFO slider sets the amount that the LFO modulates pitch. Again, this
parameter is only enabled if the LFO is on. The Key slider controls how much the oscillator tuning is
adjusted by changes in MIDI note pitch. The default value of 100% means that the oscillator will
conform to a conventional equal tempered scale. Higher or lower values change the amount of space
between the notes on the keyboard. At 0%, the oscillator is not modulated by note pitch at all. To get
a sense of how this works, try leaving one of the oscillators at 100% and setting the other’s Key
scaling to something just slightly different. Then play scales near middle C. Since C3 will always
trigger the same frequency regardless of the Key value, the oscillators will get farther out of tune with
each other the farther away from C3 you play.

The Pitch Env settings apply a ramp that modulates the oscillator’s pitch over time. Initial sets the
starting pitch of the oscillator while Time adjusts how long it will take for the pitch to glide to its final
value. You can adjust both parameters via the sliders or by adjusting the breakpoints in the envelope
display.

The Sub/Sync parameters in the display allow you to apply either a sub-oscillator or a hard
synchronization mode. When the Mode chooser is set to Sub, the Level slider sets the output level of
an additional oscillator, tuned an octave below the main oscillator. The sub-oscillator produces a
square wave when the main oscillator’s Shape control is set to rectangle or sawtooth and a sine wave
when the main oscillator is set to sine. Note that the sub-oscillator is disabled when the main
oscillator’s Shape is set to white noise.

When the Mode chooser is set to Sync, the oscillator’s waveform is restarted by an internal oscillator
whose frequency is set by the Ratio slider. At 0%, the frequency of the internal oscillator and the
audible oscillator match, so sync has no effect. As you increase the Ratio, the internal oscillator’s rate
increases, which changes the harmonic content of the audible oscillator. For maximum analog
nastiness, try mapping a modulation wheel or other MIDI controller to the Sync ratio.

28.1.3 Noise Generator

Analog’s Noise Generator.

The Noise generator produces white noise and includes its own -6db/octave low-pass filter. The
generator can be turned on or off via the Noise switch in the shell. Its output level is adjusted by the
slider to the right of this activator.

The F1/F2 slider controls the balance of the noise generator’s output to each of the two filters. When
the slider is at the center position, equal amounts of signal will be sent to both filters. When set all the
way to the top or bottom, signal will only be sent to Filter 1 or Filter 2 respectively.

The Color knob sets the frequency of the internal low-pass filter. Higher values result in more high-
frequency content.

Note that Noise has only shell parameters, so adjusting them does not change what is shown in the
display.

28.1.4 Filters

Display and Shell Parameters for the two Filters.

Analog’s two multi-mode filters come equipped with a flexible routing architecture, multiple saturation
options and a variety of modulation possibilities. As with the oscillators, all parameters can be set
independently for each filter.

The Fil 1 and Fil 2 switches in the shell toggle the respective filter on and off. The chooser next to the
filter activator selects the filter type from a selection of 2nd and 4th order low-pass, band-pass, notch,
high-pass and formant filters.

The resonance frequency of the filter is adjusted with the Freq knob in the shell, while the amount of
resonance is adjusted with the Reso control. When a formant filter is chosen in the chooser, the Reso
control cycles between vowel sounds.

Below each mode chooser is an additional control which differs between the two filters. In Filter 1, the
To F2 slider allows you to adjust the amount of Filter 1’s output that will be sent to Filter 2. The Follow
switch below Filter 2’s mode chooser causes this filter’s cutoff frequency to follow the cutoff of Filter 1.
If this is enabled, Filter 2’s cutoff knob controls the amount of offset between the two cutoff amounts. If
any of Analog’s modulation sources are controlling Filter 1’s cutoff, Filter 2 will also be affected by
them when Follow is enabled.

In addition to the envelope controls, the displays for the filters contain various modulation parameters
and the Drive chooser. Cutoff frequency and resonance can be independently modulated by LFO,
note pitch and filter envelope via the sliders in the Freq Mod and Res Mod sections respectively.
Positive modulation values will increase the cutoff or resonance amounts, while negative values will
lower them.

The Drive chooser in the display selects the type of saturation applied to the filter output. The three Sym
options apply symmetrical distortion, which means that the saturation behavior is the same for positive
and negative values. The Asym modes result in asymmetrical saturation. For both mode types, higher
numbers result in more distortion. Drive can be switched off entirely by selecting Off in the chooser.
Experiment with the various options to get a sense of how they affect incoming signals.

28.1.5 Amplifiers

Display and Shell Parameters for the two Amplifiers.

After the filters, the signal is routed to an amplifier which further shapes the sound with an amplitude
envelope and panning. All parameters can be set independently for each amplifier.

The Amp 1 and Amp 2 switches in the shell toggle the respective amplifier on and off, while the output
level is controlled by the Level knob. The Pan knob sets the position of the amplifier’s output in the
stereo field.

In addition to the envelope controls, the displays for the amplifiers contain various modulation
parameters. The Pan and Level amounts can be independently modulated by LFO, note pitch and amp
envelope via the sliders in the Pan Mod and Level Mod sections respectively. Note that, when using
note pitch as the modulation source for Level, middle C will always sound the same regardless of the
modulation amount. Positive values will cause the level to increase for higher notes.

28.1.6 Envelopes

Analog’s Envelope Parameters.

In addition to the pitch envelopes in the oscillator sections, Analog is equipped with independent
envelopes for each filter and amplifier. All four of these envelopes have identical controls, which are
housed entirely within the display. Each envelope is a standard ADSR (attack, decay, sustain, release)
design and features velocity modulation and looping capabilities.

The attack time is set with the Attack slider. This time can also be modulated by velocity via the Att <
Vel slider. As you increase the Att < Vel value, the attack time will become increasingly shorter at
higher velocities.

The time it takes for the envelope to reach the sustain level after the attack phase is set by the Decay
slider.

The Sustain slider sets the level at which the envelope will remain from the end of the decay phase to
the release of the key. When this knob is turned all the way to the left, there is no sustain phase. With it
turned all the way to the right, there is no decay phase.

The overall envelope level can be additionally modulated by velocity via the Env < Vel slider.

The S.Time slider can cause the Sustain level to decrease even if a key remains depressed. Lower
values cause the Sustain level to decrease more quickly.

Finally, the release time is set with the Release knob. This is the time it takes for the envelope to reach
zero after the key is released.

The Slope switches toggle the shape of the envelope segments between linear and exponential. This
change is also represented in the envelope visualization.

Normally, each new note triggers its own envelope from the beginning of the attack phase. With
Legato enabled, a new note that is played while another note is already depressed will use the first
note’s envelope, at its current position.

Enabling the Free switch causes the envelope to bypass its sustain phase and move directly from the
decay phase to the release phase. This behavior is sometimes called “trigger“ mode because it
produces notes of equal duration, regardless of how long the key is depressed. Free mode is ideal for
percussive sounds.

The Loop chooser offers several options for repeating certain segments of the envelope while a key is
depressed. When Off is selected, the envelope plays once through all of its segments without looping.

With AD-R selected, the envelope begins with the attack and decay phases as usual, but rather than
maintaining the sustain level, the attack and decay phases will repeat until the note is released, at
which point the release phase occurs. ADR-R mode is similar, but also includes the release phase in
the loop for as long as the key is held.

Note that in both AD-R and ADR-R modes, enabling Free will cause notes to behave as if they’re
permanently depressed.

ADS-R mode plays the envelope without looping, but plays the attack and release phases once more
when the key is released. With short attack and release times, this mode can simulate instruments with
audible dampers.

28.1.7 LFOs

Display and Shell Parameters for the two LFOs.

Analog’s two LFOs can be used as modulation sources for the oscillators, filters and amplifiers. As with
the other sections, each LFO has independent parameters.

The LFO 1 and LFO 2 switches in the shell toggle the respective LFO on and off, while the Rate knob
sets the LFO’s speed. The switch next to this knob toggles the Rate between frequency in Hertz and
tempo-synced beat divisions.

The Wave chooser in the display selects the waveform for the LFO. The choices are sine, triangle,
rectangle and two types of noise. The first noise type steps between random values while the second
uses smooth ramps. With Tri or Rect selected, the Width slider allows you to adjust the pulse width of
the waveform. With Tri selected, low Width values shift the waveform towards an upwards sawtooth,
while higher values result in a downward saw. At 50%, the waveform is a perfect triangle. The
behavior is similar with the Rect setting. At 50%, the waveform is a perfect square wave, while lower
and higher values result in negative or positive pulses, respectively. Note that Width is disabled when
the LFO’s waveform is set to sine or the noise modes.

The Delay slider sets how long it will take for the LFO to start after the note begins, while Attack sets
how long it takes the LFO to reach its full amplitude.

With Retrig enabled, the LFO restarts at the same position in its phase each time a note is triggered.
The Offset slider adjusts the phase of the LFO’s waveform.

28.1.8 Global Parameters

Display and Shell Parameters for the Global Options.

The Global shell and display parameters allow you to adjust Analog’s response to MIDI data and
controls for performance parameters such as vibrato and glide.

The Volume control in the shell adjusts the overall output of the instrument. This is the instrument’s
overall level, and can boost or attenuate the output of the amplifier sections.

The Vib switch turns the vibrato effect on or off, while the percentage slider next to it adjusts the
amplitude of the vibrato. Analog’s vibrato effect is essentially an additional LFO, but is hardwired to
the pitch of both oscillators. The Rate slider sets the speed of the vibrato.

Turning on the vibrato effect activates the four additional Vibrato parameters in the display. The Delay
slider sets how long it will take for the vibrato to start after the note begins, while Attack sets how long
it takes for the vibrato to reach full intensity. The Error slider adds a certain amount of random
deviation to the Rate, Amount, Delay and Attack parameters for the vibrato applied to each
polyphonic voice. The Amt < MW slider adjusts how much the modulation wheel will affect the vibrato
intensity. This control is relative to the value set in the vibrato amount percentage slider in the shell.

The Uni switch in the shell turns on the unison effect, which stacks multiple voices for each note played.
The Detune slider next to this switch adjusts the amount of tuning variation applied to each stacked
voice.

Turning on the unison effect activates the two additional Unison parameters in the display. The Voices
chooser selects between two or four stacked voices, while the Delay slider increases the lag time
before each stacked voice is activated.

The Gli switch turns the glide effect on or off. This is used to make the pitch slide between notes rather
than changing immediately. With Legato enabled, the sliding will only occur if the second note is
played before the first note is released. The Time slider sets the overall speed of the slide.

Turning on the glide effect activates an additional Glide Mode chooser in the display. Selecting Const
causes the glide time to be constant regardless of interval. Choosing Prop (proportional) causes the
glide time to be proportional to the interval between the notes. Large intervals will glide slower than
small intervals.

The four Quick Routing buttons on the left side of the display provide an easy way to quickly set up
common parameter routings. The upper left option configures a parallel routing structure, with each
oscillator feeding its own filter and amplifier exclusively. The upper right button is similar, but the

oscillators each split their output evenly between the two filters. The bottom left option feeds both
oscillators into Filter 1 and Amp 1, bypassing Filter 2 and Amp 2 entirely. Finally, the bottom right
option configures a serial routing structure, with both oscillators feeding Filter 1, which is then fed
exclusively to Filter 2 and Amp 2.

Note that the Quick Routing options do not affect any changes you may have made to the oscillator
level, tuning or waveform parameters — they only adjust the routing of the oscillators to the filters and
subsequent amplifiers.

The Keyboard section in the display contains all of Analog’s tuning and polyphony parameters. The
Octave, Semi and Detune controls function as coarse and fine tuners. Octave transposes the entire
instrument by octaves, while Semi transposes up or down in semitone increments. The Detune slider
adjusts tuning in increments of one cent (up to a maximum of 50 cents up or down).

PB Range sets the range of pitch bend modulation in semitones.

Stretch simulates a technique known as stretch tuning, which is a common tuning modification made to
electric and acoustic pianos. At 0%, Analog will play in equal temperament, which means that two
notes are an octave apart when the upper note’s fundamental pitch is exactly twice the lower note’s.
Increasing the Stretch amount raises the pitch of upper notes while lowering the pitch of lower ones.
The result is a more brilliant sound. Negative values simulate “negative“ stretch tuning; upper notes
become flatter while lower notes become sharper.

The Error slider increases the amount of random tuning error applied to each note.

The Voices chooser sets the available polyphony, while Priority determines which notes will be cut off
when the maximum polyphony is exceeded. When Priority is set to High, new notes that are higher
than currently sustained notes will have priority, and notes will be cut off starting from the lowest pitch.
Low is the opposite. A Priority setting of Last gives priority to the most recently played notes, cutting off
the oldest notes as necessary.

28.1.9 MPE Sources

Display Parameters for the MPE Sources.

Toggling the MPE switch in the Global section of the display reveals three MPE sources: Pressure,
Slide, and NotePB (per-note pitch bend), which can be used to further transform Analog’s sound.

You can specify up to two different destinations where MPE pressure data will be routed using the two
Pressure Destination choosers. You can set how much the MPE pressure data will modulate the
selected destinations using the MPE Pressure Amount sliders to the right.

Slide also includes two Destination choosers, each with its own MPE Slide Amount slider to control
how much the MPE slide data affects the target.

The Pressure and Slide Activity LEDs light up when Analog receives MPE pressure and slide data
respectively.

The Note PB slider sets the range of per-note pitch bend in semitones.

28.2 Collision

The Collision Instrument.

Collision is a synthesizer that simulates the characteristics of mallet percussion instruments. Created in
collaboration with Applied Acoustics Systems, Collision uses physical modeling technology to model
the various sound generating and resonant components of real (or imagined) objects.

28.2.1 Architecture and Interface

Collision’s sound is produced by a pair of oscillators called Mallet and Noise, which feed a pair of
independent (or linked) stereo resonators. While the oscillators produce the initial component of the
sound, it is the resonator parameters that have the greatest impact on the sound’s character.

Note that if both the Mallet and Noise sections are turned off, Collision will not produce any sound.

Collision’s interface is divided into sections and tabs. The Mallet and Noise sections contain controls
for the corresponding Mallet and Noise oscillators. The Resonator 1 and Resonator 2 tabs contain
parameters for both individual resonators.

The LFO tab contains two independent low-frequency oscillators (LFOs), which can each modulate
multiple parameters. Similarly, the MIDI/MPE tab allows for MIDI pitch bend, modulation wheel and

aftertouch messages and their MPE (MIDI Polyphonic Expression) equivalents to be routed to multiple
destinations.

To the right of the MIDI/MPE tab is a section of global parameters, including voice polyphony, note
retrigger, resonator structure, and overall output volume.

Note: Deactivating unused sections and tabs can help to save CPU resources.

28.2.2 Mallet Section

Collision’s Mallet Section.

The Mallet section simulates the impact of a mallet against a surface. The parameters adjust the
physical properties of the mallet itself.

You can toggle the Mallet button to switch the section on or off.

Volume controls the overall output level of the mallet. The Volume parameter can be modulated using
pitch and velocity by adjusting the Key and Vel sliders in the MIDI tab.

Stiffness adjusts the hardness of the mallet. At low levels, the mallet is soft, which results in fewer high
frequencies and a longer, less distinct impact. As you increase the stiffness, the impact time decreases
and high frequencies increase. This parameter can also be modulated by pitch and velocity via the
Key and Vel sliders in the MIDI tab.

Noise sets the amount of impact noise that is included in each mallet strike. This is useful for simulating
the “chiff“ sound of a felt-wrapped mallet head. The Noise parameter can be modulated using pitch
and velocity by adjusting the Key and Vel sliders in the MIDI tab.

Color sets the frequency of the noise component. At higher values, there are less low frequencies in
the noise. This parameter has no effect if Noise is set to 0.

28.2.3 Noise Section

Collision’s Noise Section.

Like the Mallet, the Noise section produces Collision’s initial impulse sound. The Noise oscillator
produces white noise, which is then fed into a multimode filter with a dedicated envelope generator.
This section can be used instead of, or in addition to, the Mallet section.

You can toggle the Noise button to switch the section on or off.

Next to the Noise button is a drop-down menu for the available noise filter types. You can choose
between LP, HP, BP, and LP+HP. Filter cutoff and resonance can be adjusted by using the Freq knob
and Res slider.

In BP mode, the Res slider adjusts resonance, while in LP+HP mode, it adjusts bandwidth. The filter
frequency can also be modulated by note pitch, velocity, or the envelope generator, via the Key and
Vel sliders in the MIDI tab or the Env Amt knob control.

Volume sets the overall output level of the Noise section, and can be modulated by pitch and velocity
by adjusting the Key and Vel sliders in the MIDI tab.

The Env Amt knob controls an envelope generator with standard ADSR (attack, decay, sustain,
release) options.

The attack time — how quickly Noise reaches full volume — is set with the A (Attack) slider, while the
time it takes for the envelope to reach the sustain level after the attack phase is set by the D (Decay)
slider.

The S (Sustain) slider sets the level at which the envelope will remain from the end of the decay phase
to the release of the key. When this slider is set to 0, there is no sustain phase. With it set to 100, there
is no decay phase.

Finally, the release time is set with the R (Release) slider. This is the time it takes for the envelope to
reach zero after the key is released.

The Freq knob defines the center or cut-off frequency of the filter. The Res slider sets the resonance of
the filter frequency in LP, HP, and BP filters, and the width of the LP+HP filter.

28.2.4 Resonator Tabs

Collision’s Resonators.

The majority of Collision’s character is determined by the parameters in the two Resonator tabs. Each
resonator can be toggled on or off via the switch in its tab. Keep in mind that if both resonators are
turned off, no sound will be produced.

At the top of the Resonator tab, you will see a Resonance Type drop-down menu of resonant objects:

•
•

•
•

•

•

•

Beam simulates the resonance properties of beams of different materials and sizes.
Marimba, a specialized variant of the Beam model, reproduces the characteristic tuning of
marimba bar overtones which are produced as a result of the deep arch-cut of the bars.
String simulates the sound produced by strings of different materials and sizes.
Membrane is a model of a rectangular membrane (such as a drum head) with a variable size
and construction.
Plate simulates sound production by a rectangular plate (a flat surface) of different materials
and sizes.
Pipe simulates a cylindrical tube that is fully open at one end and has a variable opening at the
other (adjusted with the Opening parameter.)
Tube simulates a cylindrical tube that is closed at both ends.

Selecting an object adds a visualization of it to the X-Y Controller display.

Next to the Resonance Type drop-down is a Quality menu with options ranging from Eco to High.
Quality controls the trade-off between the sound quality of the resonators and CPU performance by
reducing the number of overtones that are calculated. Eco uses minimal CPU resources, while High
creates more sophisticated resonances. Note that the Pipe or Tube resonators do not offer a Quality
menu.

Each resonator contains a copy button (1 → 2 in Resonator 1 and 2 → 1 in Resonator 2) that you
can use to copy all the settings from one resonator to the other.

Using the X-Y Controller, you can click and drag the mouse horizontally to change the resonant
object’s decay time, or vertically to change the value of the Material/Radius parameter.

The decay time adjusts the amount of the internal damping in the resonator and can also be adjusted
using the Decay slider.

The Material slider adjusts the variation of damping at different frequencies. At lower values, low
frequency components decay slower than high frequency components (which simulates objects made
of wood, rubber, or nylon). At higher values, high frequency components decay slower (which
simulates objects made of glass or metal).

In the Pipe and Tube resonators, a Radius parameter is available in place of the Material parameter.
This slider adjusts the radius of the pipe or tube. As the radius increases, the decay time and high
frequency sustain both increase. At very large sizes, the fundamental pitch of the resonator also
changes.

The Decay and Material/Radius parameters can be modulated by note pitch and velocity via the Key
and Vel sliders in the MIDI tab.

An additional Ratio parameter is available for the Membrane and Plate resonators, which adjusts the
ratio of the object’s size along its x and y axes.

The Brightness control adjusts the amplitude of various frequency components. At higher values, higher
frequencies are louder. This parameter is not used with the Pipe or Tube resonators.

The Inharm knob adjusts the pitch of the resonator’s harmonics. At negative values, frequencies are
compressed, increasing the number of lower partials. At positive values, frequencies are stretched,
increasing the number of upper partials. Inharm can also be modulated by velocity via the slider in
the MIDI tab. Note that this parameter is not used with the Pipe or Tube resonators.

Opening, which is only available for the Pipe resonator, scales between an open and closed pipe. At
0%, the pipe is fully closed on one side, while at 100% the pipe is open at both ends. This parameter
can also be modulated by velocity in the MIDI tab.

The Hit slider adjusts the location on the resonator at which the object is struck or otherwise activated.
At 0%, the object is hit at its center. Higher values move the activation point closer to the edge. The Hit
position can also be randomized by increasing the value of the Rnd slider. Note that this parameter is
not used with the Pipe or Tube resonators.

Note Off determines the extent to which MIDI Note Off messages mute the resonance. At 0%, Note
Offs are ignored, and the decay time is based only on the value of the Decay parameter. This is
similar to how real-world mallet instruments behave, such as marimbas and glockenspiels. At 100%,
the resonance is muted immediately at Note Off, regardless of the Decay time.

The Pos. L and Pos. R sliders adjust the location on the left and right resonator where the vibrations are
measured. At 0%, the resonance is monitored at the object’s center. Higher values move the listening
point closer to the edge. These parameters are not used with the Pipe or Tube resonators, which are
always measured in the middle of their permanently open end.

28.2.4.1 Tuning Section

Resonator Tuning Parameters.

The Tune knob and Fine slider function as coarse and fine tuning controls. Tune moves up or down in
semitone increments, while Fine adjusts in increments of one cent (up to a maximum of one quarter
tone (50 cents) up or down).

The Tune knob can also be modulated via the Key slider in the MIDI tab. The Key slider sets how much
the resonator’s tuning is adjusted by changes in MIDI note pitch. The default value of 100% means
that the resonator will conform to a conventional equal tempered scale. At 200%, each half step on
the keyboard will result in a whole step change in tuning. At negative values, the resonator will drop in
pitch as you play higher on the keyboard.

The Pitch Envelope parameters (Pitch Env and Time) apply a ramp that modulates the resonator’s pitch
over time. Pitch Env sets the starting pitch while Time adjusts how long it will take the pitch to glide to
its final value. The starting pitch can be modulated by velocity via the corresponding Vel slider in the
MIDI tab.

28.2.4.2 Mixer Section

Resonator Mixer.

Each resonator has its own Gain and Pan controls. Pan can also be modulated by note pitch via the
Key slider in the MIDI tab.

The Bleed control mixes a portion of the original oscillator signal with the resonated signal. At higher
values, more of the original signal is applied. This is useful for restoring high frequencies, which can
often be damped when the tuning or quality are set to low values.

Gain adjusts the output level of the selected resonator.

28.2.5 LFO Tab

Collision’s LFOs.

Collision’s two independent LFOs can be used as modulation sources for a variety of mallet, noise,
and resonator parameters, which are selectable in the Destination choosers. Additionally, they can
modulate each other.

The LFO 1 and LFO 2 switches toggle the respective LFO on and off, while the waveform chooser
determines the wave shape. The choices are sine, square, triangle, sawtooth up, sawtooth down and
two types of noise. The first noise type steps between random values while the second uses smooth
ramps.

The Offs. slider sets the phase offset of the LFO. When Retrigger is enabled, triggering a note restarts
the LFO with the waveform phase set by the Offset parameter.

Each LFO can modulate two targets, which are set via the Destination choosers. The intensity of the
modulations is adjusted with the LFO Destination Amount sliders. Note that these modulation amounts
are relative to the LFO’s Amount value.

Rate adjusts the speed of the LFO and can be set in Hertz or tempo-synced beat divisions. The Amount
knob determines the overall intensity of the LFO. Rate can be modulated by note pitch and Amount by
velocity in the MIDI tab.

28.2.6 MIDI/MPE Tab

Collision’s MIDI/MPE Tab.

The MIDI/MPE tab allows for a wide variety of internal MIDI mappings, both for standard and MPE-
enabled MIDI controllers. A MIDI controller’s pitch bend (including per-note pitch bend), modulation
wheel, pressure and slide signals can be mapped to two destinations each, with independent
modulation intensities set via the Amount sliders.

Additional mallet, noise, resonator, and LFO parameters can be modulated using pitch or velocity
using the Key and Vel sliders.

28.2.6.1 The Global Section

Collision’s Global Section.

The global section contains the parameters that relate to the overall behavior and performance of
Collision.

The Voices drop-down menu lets you set the maximum number of notes that can sound simultaneously.

When Retrig. is on, notes which are already playing will be retriggered, rather than generating an
additional voice. This can help to save CPU resources.

Structure determines the signal flow through the resonators.

In serial mode 1 > 2 both resonators output to Resonator 1. Resonator 1 is then mixed down to mono
and routed to Resonator 2, as well as its own mixer (in stereo).

Resonators in 1 > 2 (Serial) Configuration.

In parallel mode 1 + 2 the output from the Mallet and Noise sections is mixed and then sent directly to
both resonators.

Resonators in 1 + 2 (Parallel) Configuration.

Volume sets the overall volume output.

28.2.7 Sound Design Tips

Although Collision has been designed to model the behavior of objects that exist in the physical
world, it is important to remember that these models allow for much more flexibility than their physical
counterparts. While Collision can produce extremely realistic simulations of conventional mallet
instruments such as marimbas, vibraphones and glockenspiels, it is also very easy to “misuse“ the
instrument’s parameters to produce sounds which could never be made by an acoustic instrument.

To program realistic instrument simulations, it helps to think about the chain of events that produces a
sound on a mallet instrument (a marimba, for example), and then visualize those events as sections
within Collision:

•
•

A beater (Mallet) strikes a tuned bar (Resonator 1).
The tuned bar’s resonance is amplified by means of a resonating tube (Resonator 2).

Thus the conventional model consists of the Mallet Exciter and the two resonators in a serial (1 > 2)
configuration.

Of course, to program unrealistic sounds, anything goes:

•

•
•

Try using the Noise Exciter, particularly with long envelope times, to create washy, quasi-
granular textures. These parameters can also be used to simulate special acoustic effects such
as bowed vibraphones or crystal glasses.
Experiment with the resonators in parallel (1 + 2) configuration.
Use the LFOs and MIDI controllers (including MPE-enabled ones) to modulate Collision’s
parameters.

A word of caution: in many ways, Collision’s models are idealized versions of real-world objects.
Consequently, it is very easy to program resonances that are much more sensitive to input than any
physical resonator could be. Certain combinations of parameters can cause dramatic changes in
volume. Make sure to keep output levels low when experimenting with new sounds.

28.3 Drift

The Drift Instrument.

Drift is a versatile synthesizer with intuitive controls and a simple interface that is fully MPE-capable.
Based on subtractive synthesis, Drift has been carefully built for quick and easy sound design while
using minimal CPU resources.

Drift’s interface is divided into six main sections: an oscillator section, a dynamic filter section, an
envelopes section, two modulation sections (LFO and Mod), and a section of global controls.

28.3.1 Subtractive Synthesis

Subtractive synthesis is a technique that generally starts with a waveform that is then shaped using
filters to sculpt the original timbres into new forms. In addition to this process, Drift offers many
modulation options for tweaking and customizing the sound even more, allowing you to easily create
a wide variety of sounds. The signature Drift control lets you add pitch and frequency variation to
each voice, resulting in a slightly detuned, fluctuating pulse throughout the tone.

28.3.2 Oscillator Section

Drift’s Oscillator Section.

Drift’s Oscillator section features two separate oscillators, pitch modulation controls, a waveform
display, an oscillator mixer, and a noise generator.

28.3.2.1 Oscillator 1

You can select from several curated waveforms using the Osc 1 drop-down menu: Sine, Triangle,
Shark Tooth, Saturated, Saw, Pulse, and Rectangle. The Shark Tooth and Saturated waveforms are
unique to Drift; Shark Tooth is based on a classic Moog analog shape with the same name, while
Saturated works well for bass sounds.

The Oct knob transposes Oscillator 1 in octaves. You can use the Shape knob to change the harmonic
content of the waveform into something slightly different, resulting in an effect similar to pulse-width
modulation. As the timbre varies between each waveform, they all respond differently to the Shape
control. When you make adjustments to the control, you can view the result in the Waveform Display
located at the bottom of the Oscillator section. You’ll notice how the waveform changes as you tweak
the Shape value.

To the right of the Shape knob, the Oscillator 1 Shape Mod Source drop-down lets you select a
modulation source that will affect the Shape control, allowing you to further morph the waveform:

•
•

•
•

•

•
•
•

Env 1
Env 2/Cyc - Envelope 2 or the Cycling Envelope can be used for modulation, depending on
which is activated.
LFO
Key - When the Shape Mod Amount is set to a positive value, higher note pitches will produce
more modulation and lower pitches less, and vice versa when the amount is set to a negative
value.
Velocity - Incoming velocity data will be used for modulation; higher note velocities will
produce more modulation and lower note velocities less.
Modwheel
Pressure
Slide

You can set the amount of modulation anywhere between -100% to 100% using the Oscillator 1
Shape Mod Amount slider. Note that Shape Mod can also introduce modulation to the waveform
when set between values of 1% - 100%, even if the Shape control value itself is set to 0%.

28.3.2.2 Oscillator 2

Using the Osc 2 drop-down menu, you can select a waveform for the second oscillator: Sine,
Triangle, Saturated, Saw, and Rectangle.

The Oct knob transposes Oscillator 2 in octaves, while the Detune control offers transposition in
semitones.

28.3.2.3 Pitch Mod

The Pitch Mod section contains two modulation source options, which will affect the pitch of both
oscillators. You can choose Env 1, Env 2 / Cyc, LFO, Key, Velocity, Modwheel, Pressure, or Slide as a
modulation source using the Oscillator Pitch Mod Source drop-down menus. The Oscillator Mod
Amount sliders determine how much each source modulates the pitch within a range from -100% to
100%.

When applying pitch modulation using an LFO that uses the Ratio time mode, it is possible to generate
FM tones.

28.3.2.4 Waveform Display

Drift’s Waveform Display.

The waveform display shows the result of the combined output of Osc 1, Osc 2 and the noise
generator, if enabled. As you make adjustments to the oscillators, you will see how the waveform
changes in the display.

28.3.2.5 Oscillator Mixer

Drift’s Oscillator Mixer.

In Drift’s Oscillator Mixer, you can enable Oscillator 1 and 2, as well as a noise generator that adds
white noise to the overall waveform shape, by using the respective switches.

You can also set the gain for each oscillator and the noise generator with the Osc 1, Osc 2, and
Noise controls. When filter processing is on, high oscillator gain values can reach the maximum
“headroom” of the filters, at which point they stop functioning linearly, resulting in a complex distortion
similarly found in analog hardware.

There are two saturation points in the filter circuits that cause this distortion, one before the filter and
one after. As the oscillator gain values are increased from the default -6.0 dB, the first saturation point
will become activated, and the second will be triggered when gain values are above 0.0 dB.

Enabling the arrow toggles to the right of the gain controls switches on filter processing for the
oscillators and noise generator. If filter processing is switched off, the oscillator and noise generator
output bypasses the filter completely.

The R toggle switches Retrigger for the oscillators on or off. If Retrigger is on, the phase of both
oscillators is reset to the same position each time a note is played; if switched off, the oscillators are
free-running.

28.3.3 Filter Section

Drift’s Filter Section.

Filtering plays an important role in shaping the timbres produced by the oscillators.

Drift’s Filter section has a low-pass filter that can be switched between two filter types, filter key
tracking, a resonance control, a high-pass filter, and two frequency modulation controls.

The Freq knob sets the cutoff frequency of the low-pass filter. You can use the Type toggle to switch
between two distinct low–pass filters: Type I (12 dB/octave) and Type II (24 dB/octave).

Type I uses a DFM-1 filter which feeds back more of its distortion internally, resulting in a broad range
of tones from subtle filter sweeps to warm drive.

Type II has the Cytomic MS2 filter which uses a Sallen-Key design and soft clipping to limit
resonance.

The Key slider determines how the pitch of incoming MIDI notes influences the low-pass filter’s
frequency. If set to 0.00, MIDI notes have no effect on filter frequency. If set to 1.00, the filter
frequency will be lower for low notes and higher for high notes.

The Res knob adjusts the resonance of the low-pass filter, while the HP knob sets the cutoff frequency
for the high-pass filter.

You can also click anywhere in the Filter section to access and adjust the envelope using the display in
the Envelopes section with an X-Y controller. You can drag the left filter dot horizontally to set the high-
pass frequency. The right filter dot adjusts the low-pass frequency when dragged horizontally or the
resonance amount when dragged vertically.

You can select up to two modulation sources for the low-pass filter cutoff frequency using the Low-
pass Modulation Source drop-down menus in the Freq Mod section. The Low-pass Modulation
Amount sliders let you determine how much each source modulates the frequency within a range from
-100% to 100%.

28.3.4 Envelopes Section

Drift’s Envelopes Section.

Envelopes generally determine how the amplitude of the sound changes from the moment a note is
played to when it is released.

Drift’s Envelopes section contains two separate envelopes: one which controls how the amplitude
changes and another that can be used specifically for modulation.

28.3.4.1 Envelope 1

Envelope 1 determines how the amplitude of the Oscillator section’s output (including both oscillators,
as well as the Noise generator if enabled) begins and changes when a note is played and then
released.

You can set the Attack, Decay, Sustain, and Release controls using the respective knobs or by
adjusting the envelope itself in the display.

Attack sets the time needed to travel from the initial value to the peak value.

Decay sets the time needed to travel from the peak value to the Sustain level.

Sustain sets the level reached at the end of the Decay stage; the envelope will remain at this level until
the note ends.

Release sets the time needed to travel back to zero after the note is released.

You can toggle between Envelope 1 and Envelope 2 by clicking the respective section in the UI, or by
using the 1 and 2 toggles in the display. The selected envelope will be shown in the display for
editing.

28.3.4.2 Envelope 2

Envelope 2 also has Attack, Decay, Sustain and Release controls however, unlike Envelope 1,
Envelope 2 is not mapped to amplitude by default, and can be used as a source for all modulation
source options within Drift.

Envelope 2 can be changed from an ADSR envelope to a Cycling Envelope by toggling the switch to
the left of the Attack control.

Cycling Envelope.

The Cycling Envelope functions similarly to an LFO modulation that restarts with each incoming MIDI
note.

The Tilt knob moves the midpoint of the envelope, at very low or high amounts this can also affect the
envelope’s slopes. The Hold control defines how long the envelope stays at its maximum level.

By default, the Cycling Envelope displays the Rate control, which is one of four possible time modes,
also including Ratio, Time, or Sync. You can select the other modes by clicking the switches to the right
of the control. Depending on the time mode, the repetition rate can be set in Hz, ratio, milliseconds, or
tempo-synced beat divisions.

28.3.5 LFO Section

Drift’s LFO Section.

Like the Cycling Envelope, Drift’s LFO can be set in one of four different time modes: Rate, Ratio, Time,
or Sync. The time mode determines the repetition rate of the LFO in Hz, ratio, milliseconds, or tempo-
synced beat divisions.

In the LFO display, you can select from nine different waveforms using the drop-down menu:

•
•
•
•
•
•
•

•
•

Sine
Triangle
Saw Up
Saw Down
Square
Sample & Hold
Wander is a sample and hold with an S-shape which interpolates between two values at the
rate of the LFO.
Linear Envelope is a one-shot decay envelope with a linear decay.
Exponential Envelope is a one-shot decay envelope with an exponential decay.

You can use the R switch to turn Retrigger on or off. If on, the LFO resets to the same position in its
phase each time a note is triggered. If off, the LFO is free-running.

The LFO Amount knob sets the overall intensity of the LFO. The LFO Modulation Source drop-down
menu lets you select a modulation source for the LFO, while the LFO Modulation Amount slider
determines how much that modulation is applied to the LFO.

28.3.6 Mod Section

Drift’s Mod Section.

Most of Drift’s parameters can be modulated; you can select up to three modulation sources and
destinations in the Mod section.

You can choose from the following sources using the Modulation Source choosers: Env 1, Env 2 /
Cyc, LFO, Key, Velocity, Modwheel, Pressure, or Slide.

The following destinations are available in the Modulation Destination choosers: Osc 1 Gain, Osc 1
Shape, Osc 2 Gain, Osc 2 Detune, Noise Gain, LP Frequency, LP Resonance, HP Frequency, LFO
Rate, Cyc Env Rate, and Main Volume.

You can use the Modulation Amount sliders to set how much the modulation destination is affected by
the modulation source within a range of -100% to 100%.

28.3.7 Global Section

Drift’s Global Section.

Drift’s global controls affect the overall behavior and performance of the instrument.

The Mode chooser lets you select from Drift’s four different Voice Modes:

Poly uses one voice per note and offers up to 32 voices of polyphony.

Mono plays one note at a time, but the note is rendered using four voices to produce a unison effect
depending on the Mono Thickness value. The Mono Thickness slider lets you adjust the relative volume
of the four voices associated with each note. When Thickness is set to 0, only one voice will be played
for a note. As Mono Thickness is set to higher values, the volume of the other three voices increases so
that they become audible with each note. A new note will choke the previously played note, if it is still
being held.

Stereo uses two voices per note and pans them to the left and right. The Stereo Spread slider sets how
much panning variation is applied across the individual voices. At higher amounts, the voices are
further apart, producing a widening effect.

Unison slightly detunes the four voices for each note independently from one another. The Unison
Strength slider determines how much pitch variation is applied across individual voices. When set to
higher values, more variation is added to each voice.

You can select the maximum number of voices that can play simultaneously using the Voices drop-
down menu. Certain Voice Modes can utilize more voices than notes played, meaning that
depending on which Voice Mode is selected, the polyphony will be different. For example, when the
Voices amount is set to 32 voices:

•
•
•

Poly mode uses 1 voice per note and has a maximum of 32-note polyphony.
Stereo mode uses 2 voices per note and has a maximum of 16-note polyphony.
Unison mode uses 4 voices per note and has a maximum of 8-note polyphony.

The Drift slider adds slight variation to each voice, affecting different aspects of the voice’s sound, such
as pitch and filter cutoff. Every voice in Drift has a different randomization for the oscillators and filter
frequency; adjusting the Drift control increases or decreases this unique randomization. At higher
amounts, the gaps between the oscillators and the filter widens, making the sound more out of tune.

When the Voice Mode is set to Mono, you can enable the Legato switch so that triggering a new
voice will change its pitch without resetting its envelopes. The Glide slider lets you adjust the time
overlapping notes take to slide their pitch to the next incoming pitch when notes are played legato.

The Volume knob sets the overall volume for the instrument, while the Vel > Vol slider determines how
much the volume will be modulated by incoming MIDI note velocity.

The Transpose slider lets you adjust the global pitch in semitones within a range of -48 to 48 st. You
can switch on the Note PB toggle to enable per-note pitch bend. Switching Note PB off lets you use
an MPE controller without having the pitch change based on finger position. The PB Range slider sets
the global pitch bend range in semitones.

28.4 Drum Sampler

The Drum Sampler Instrument.

Drum Sampler is an instrument designed for playing back one-shot samples in Drum Racks. It offers
key sampler features such as start and length controls, an AHD amplitude envelope, and pitch
controls. Drum Sampler also includes a filter section, modulation options, and a set of dedicated
playback effects for manipulating samples in various ways.

28.4.1 Sample Controls Section

Drum Sampler’s Sample Controls Section.

In the Sample Controls section, you can modify the sample’s envelope, pitch, and volume, as well as
swap out a loaded sample.

To load a sample into Drum Sampler, double-click a file in the browser or drag and drop it onto the
waveform display.

The Sample Start slider sets the point where sample playback begins, calculated as a percentage of
the sample’s length. Hold Shift while dragging the slider to adjust the start point in fine increments.

The Sample Length slider sets the length of the region that is played, calculated as a percentage of the
sample’s total length.

You can use the Sample Gain slider to adjust the volume of the sample, from -70 to 24 dB.

Adjusting the Sample Start, Sample Length, and Sample Gain controls also updates the waveform in
the display.

You can use the Attack, Hold, and Decay controls to adjust the sample’s envelope.

Attack sets the time needed to travel from the envelope’s initial level to its peak level.

Hold sets the time the envelope’s amplitude level remains at the peak level after reaching the attack
time. This parameter is disabled when the device’s Envelope Mode is set to Gate.

Decay sets the time needed to travel from the peak level back to zero after the Hold time is reached in
Trigger mode, or once the note is released in Gate mode.

The Transpose slider sets the global transposition amount, from -48 to 48 semitones, while the Detune
slider sets the global detune amount, from -50 to 50 cents.

Drum Sampler offers two envelope modes: Trigger and Gate. In Trigger mode, the sample continues
to play for the duration of the set Hold time after a note is released. In Gate mode, the sample fades
out according to the set Decay time once a note is released.

Hovering over the waveform display reveals additional controls for managing the loaded sample.

The Similar Sample Swapping and Hot-Swap Controls.

Use the Swap to Next Similar Sample button to cycle through samples that sound similar to the
original file. To go back through the options, click the Swap to Previous Similar Sample button. You
can also right-click the display and select Show Similar Files to access a list of similar samples in the
browser.

When cycling through samples, you can return to the initially loaded file by right-clicking the
waveform display and selecting Return to Reference. To set the currently loaded file as a new
reference for swapping, use the Save as Similarity Reference option.

The hot-swap button opens the Hot-Swap Browser, where you can replace the loaded sample with a
different one. To replace Drum Sampler with another instrument, use the hot-swap button in the
device’s title bar.

28.4.2 Playback Effects Section

Drum Sampler’s Playback Effects Section.

You can apply one of nine playback effects to further sculpt a sample’s sound: Stretch, Loop, Pitch Env,
Punch, 8-Bit, FM, Ring Mod, Sub Osc, and Noise.

Each playback effect has two parameters, which can be adjusted via dedicated knobs or by using the
X/Y pad. Drag vertically on the X/Y pad to adjust the first parameter, and drag horizontally to adjust
the second.

Use the Playback Effect On toggle to turn this section on or off. When enabled, you can select an
effect from the Playback Effect Type drop-down menu.

Stretch changes the sample’s length without altering its pitch. This produces granular artifacts, which
add lo-fi texture to the sound. The Factor control sets the amount of time-stretching as a multiple of the
original playback speed. The Grain Size control sets the size of the grain used to time-stretch the
sample in milliseconds.

Loop repeats a portion of the sample. The Loop Offset control sets the loop start point relative to the
sample start. The Loop Length control sets the loop’s duration in milliseconds.

Pitch Env uses an envelope to modulate the pitch of the sample over time. The Pitch Envelope Amount
control sets the amount of pitch modulation applied, from -100 to 100%. Positive values result in a
higher pitch, while negative values result in a lower pitch. The Pitch Envelope Decay control sets the
time it takes for the pitch to return to the base value as defined by the device’s global pitch controls.

Punch applies ducking with a fixed attack and an envelope shaped to emphasize the sample’s
transient. The Punch Amount control sets the amount of ducking applied. The Punch Release control
determines how long it takes for the gain reduction to return to zero after the initial trigger.

8-Bit applies a combination of filtering, bit reduction, and sample rate reduction to recreate the sound
of 8-bit CPU chips. The 8-Bit Sample Rate control sets the sample rate at which the sample is played
back. The 8-Bit Decay Time control sets the decay time of the effect’s built-in low-pass filter.

FM uses a sine wave to modulate the sample’s pitch. The Amount control sets the intensity of the
frequency modulation, while the FM Frequency control sets the frequency used to modulate the
sample’s pitch.

Ring Mod applies ring modulation to the sample. The Amount control sets how much modulation is
applied. The Ring Mod Frequency control sets the frequency used to modulate the sample’s amplitude.
Low values produce a tremolo effect, while high values produce artifacts that are typical of ring
modulation.

Sub Osc layers a sub oscillator with the sample. The Sub Oscillator Amount knob sets the oscillator’s
level. The oscillator envelope uses the device’s attack and decay settings. The Sub Oscillator
Frequency sets the oscillator’s frequency, from 30 to 120 Hz.

Noise Osc layers a noise oscillator with the sample. The Noise Amount knob sets the oscillator’s level.
The oscillator envelope uses the device’s attack and decay settings. The Noise Color control sets the
frequency used to filter the oscillator.

Note that time-based and frequency-related controls in the Stretch, Loop, FM, Ring Mod, Sub Osc,
and Noise Osc effects are influenced by the device’s global pitch controls and the MIDI note played.
This ensures that each effect’s pitch follows the pitch of the sample as different notes are played or
when the sample is transposed.

Additionally, the modulation decay of the FM and Ring Mod effects is affected by the global decay
time. For example, with short decay times, modulation is applied only to the sample’s transient.

28.4.3 Filter Section

Drum Sampler’s Filter Section.

Use the Filter On toggle to turn the filter on or off.

There are four filter types to choose from: a 12 dB low-pass filter, a 24 dB low-pass filter, a 24 dB
high-pass filter, and a peak filter.

The low and high-pass filters include dedicated Resonance and Filter Frequency controls. When the
peak filter is selected, you can use the Peak Filter Gain and Filter Frequency controls to boost or cut a
specific frequency range.

28.4.4 Global Section

Drum Sampler’s Global Section.

In the Global Section, you can adjust the output volume, panning, velocity-to-volume ratio, and
modulation parameters.

The Volume control sets the device’s global output level, from -36 to 36 dB, while the Pan slider
adjusts the stereo position.

The Velocity to Volume slider determines how much the device’s volume is modulated by incoming
MIDI note velocity.

Use the Modulation Source toggle to switch between two modulation sources: Velocity or Slide
(MPE). Then select a modulation target from the Modulation Destination drop-down menu.

The Filter target modulates the filter cutoff frequency.

You can modulate any of the individual envelope stages with the Attack, Hold, and Decay targets.

Use FX1 and FX2 to modulate the two parameters of the currently selected playback effect.

The Modulation Amount slider sets the amount of modulation that is applied to the target.

28.4.5 Context Menu Options for Drum Sampler

In addition to the usual device context menu entries, there are also a couple of options unique to Drum
Sampler.

Enable Per-Note Pitch Bend — This option allows Drum Sampler to receive per-note pitch bend
messages and is enabled by default.

Drum Sampler > Simpler — This replaces Drum Sampler with Simpler, retaining the sample’s start and
length positions.

When using Drum Racks, you can select the Save as Default Pad option from a pad’s context menu to
use Drum Sampler as the default for new samples.

The Save as Default Pad Option.

This means that each time a sample is added to an empty drum pad, an instance of Drum Sampler is
automatically loaded.

28.5 Electric

The Electric Instrument.

Electric is a software electric piano developed in collaboration with Applied Acoustics Systems. It is
based on the classic instruments of the seventies; each component has been modeled using cutting
edge physical modeling technology to provide realistic and lively sounds.

Physical modeling uses the laws of physics to reproduce the behavior of an object. In other words,
Electric solves, in real time, mathematical equations describing how its different components function.
No sampling or wavetables are used in Electric; the sound is calculated in real time by the CPU
according to the values of each parameter. Electric is more than a simple recreation of vintage
instruments; its parameters can be tweaked to values not possible with the real instruments to get some
truly amazing new sounds that still retain a warm acoustic quality.

28.5.1 Architecture and Interface

The mechanism of the electric piano is actually quite simple. A note played on the keyboard activates
a hammer that hits a fork. The sound of that fork is then amplified by a magnetic coil pickup and sent
to the output, very much like an electric guitar. The fork is made of two parts, called the tine bar and
tone bar. The tine bar is where the hammer hits the fork while the tone bar is a tuned metal resonator,
sized appropriately to produce the correct pitch. Once the fork is activated, it will continue to resonate
on its own for a long time. But releasing the key applies a damper to the fork, which mutes it more
quickly.

The Electric interface is divided into four main sections: Hammer, Fork, Damper/Pickup, which contain
parameters pertaining to the instrument’s tone and sound; and the Global section which contains
parameters that affect overall behavior and performance, such as pitch bend and polyphony.

You can click on the individual sections to reveal all of their associated parameters, or you can click
on the Hammer, Fork, or Damper/Pickup icons to toggle between those respective sections.

Electric’s Hammer, Fork, and Damper/Pickup Icons.

28.5.2 Hammer Section

Electric’s Hammer Section.

The Hammer section contains the parameters related to the physical properties of the hammer itself, as
well as how it’s affected by your playing.

The Stiffness knob adjusts the hardness of the hammer’s striking area. Higher values simulate a harder
surface, which results in a brighter sound. Lower values mean a softer surface and a more mellow
sound. Stiffness can also be modified by velocity and note pitch via the Vel and Key sliders in the
bottom half of the display.

The Noise knob adjusts the amount of impact noise caused by the hammer striking the fork. In the
Noise section in the bottom half of the display, the Pitch slider sets the center frequency of the noise
pitch, while the Decay slider adjusts how long it takes for the noise to fade to silence. The Key slider
controls how much the noise volume is determined by note pitch.

The Force section adjusts the intensity of the hammer’s impact on the fork. Low Amount values simulate
a soft impact while high values result in a hard impact. Force can also be modified by velocity and
note pitch, via the Vel and Key sliders.

28.5.3 Fork Section

Electric’s Fork Section.

The Fork section contains knobs for both Tine and Tone parameters, which are the heart of Electric’s
sound generating mechanism.

Tine controls the portion of the fork that is directly struck by the hammer.

The Color slider controls the relative amplitude of high and low partials in the tine’s spectrum. Low
values result in lower harmonics, while higher values result in higher harmonics.

The Decay knob adjusts how long it takes the tine’s sound to fade out while a note is held. The volume
level of the tine can be modulated by note pitch via the Key slider.

Tone controls the secondary resonance of the fork.

The Release slider applies to both Tine and Tone, and controls the decay time of the fork’s sound after
a key is released. The Decay parameter works in the same way as in the Tine subsection.

28.5.4 Damper/Pickup Section

Electric’s Damper/Pickup Section.

28.5.4.1 Pickup Parameters

In Electric, the Pickup simulates the behavior of the magnetic coil pickup that amplifies the sound of the
resonating fork.

The Symmetry knob and Distance slider adjust the physical location of the pickup in relation to the
tine. Symmetry simulates the vertical position of the pickup. At 50%, the pickup is directly in front of the
tine, which results in a brighter sound. Lower amounts move the pickup below the tine, while higher
amounts move it above the tine. Distance controls how far the pickup is from the tine. Higher amounts
increase the distance, while lower amounts move the pickup closer. Note that the sound becomes
more overdriven as the pickup approaches the tine.

The Type R and W buttons switch between two different types of pickups. In the R position, Electric
simulates electro-dynamic pickups, while W is based on an electro-static model.

The Input slider is used to adjust the amount of the fork’s signal that is fed to the pickup, which in turn
affects the amount of distortion applied to the overall signal. The Output slider controls the amount of
signal output by the pickup section. Different combinations of these two parameters can yield very
different results. For example, a low amount of input with a high amount of output will produce a
cleaner sound than a high input with a low output. The output level can be further modulated by note
pitch via the Key slider.

28.5.4.2 Damper Parameters

The metal forks in an electric piano are designed to sustain for a long time when a key is held. The
mechanism that regulates this sustain is called the damper. When a key is pressed, that note’s damper
is moved away from its fork. When the key is released, the damper is applied to the fork again to stop

it from vibrating. But the dampers themselves make a small amount of sound, both when they are
applied and when they are released. The Damper parameters simulate this characteristic noise.

The Tone slider adjusts the stiffness of the dampers. Lower values simulate soft dampers, which
produces a mellower sound. Higher values increase the hardness of the dampers, producing a
brighter sound. The overall amount of damper noise is adjusted with the Level slider.

The Att/Rel slider adjusts whether or not damper noise is present when the dampers are applied to the
fork or when they are released. At -100, damper noise will only be heard during the note’s attack
phase. At 100, the noise is present only during the release phase. In the center, an equal amount of
noise will be present during both attack and release.

28.5.5 Global Section

Electric’s Global Section.

The Global section contains the parameters that relate to the overall behavior and performance of
Electric.

The Volume knob sets Electric’s overall output level.

The Voices chooser sets the available polyphony. Since each voice that’s used requires additional
CPU, you may need to experiment with this setting to find a good balance between playability and
performance.

The Semi and Detune sliders function as coarse and fine tuners. Semi transposes the entire instrument
up or down in semitone increments, while the Detune slider adjusts in increments of one cent (up to a
maximum of 50 cents up or down).

Stretch simulates a technique known as stretch tuning, which is a common modification made to both
electric and acoustic pianos and is an intrinsic part of their characteristic sound. At 0%, Electric will
play in equal temperament, which means that two notes are an octave apart when the upper note’s
fundamental pitch is exactly twice the lower note’s. But because the actual resonance behavior of a

vibrating tine or string differs from the theoretical model, equal temperament tends to sound “wrong“
on pianos. Stretch tuning attempts to correct this by sharpening the pitch of upper notes while
flattening the pitch of lower ones. The result is a more brilliant sound. Negative values simulate
“negative“ stretch tuning; upper notes become flatter while lower notes become sharper.

Pitch Bend sets the range in semitones of global pitch bend modulation, while Note PB sets the MPE
per-note pitch bend range in semitones.

28.6 External Instrument

The External Instrument.

The External Instrument device is not an instrument itself, but rather a routing utility that allows you to
easily integrate external (hardware) synthesizers and multitimbral plug-ins into your projects. It sends
MIDI out and returns audio.

The two MIDI To choosers select the output to which the device will send MIDI data. The top chooser
selects either a physical MIDI port, or a multitimbral plug-in. If you select a MIDI port (for use with an
external synthesizer), the second chooser’s options will be MIDI channel numbers.

If another track in your Set contains a multitimbral plug-in, you can select this track in the top chooser.
In this case, the second chooser allows you to select a specific MIDI channel in the plug-in.

The Audio From chooser provides options for returning the audio from the hardware synth or plug-in
device. If you’re routing to a hardware synth, use this chooser to select the ports on your audio

interface that are connected to the output of your synth. The available choices you’ll have will depend
on the settings in the Audio Settings.

If you’re routing to a multitimbral plug-in on another track in your Live Set, the Audio From chooser will
list the auxiliary outputs in the plug-in. Note that the main outputs will be heard on the track that
contains the instrument.

The Gain knob adjusts the audio level coming back from the sound source. This level should be set
carefully to avoid clipping.

Since external devices can introduce latency that Live cannot automatically detect, you can manually
compensate for any delays by adjusting the Hardware Latency slider. The button next to this slider
allows you to set your latency compensation amount in either milliseconds or samples. If your external
device connects to Live via a digital connection, you will want to adjust your latency settings in
samples, which ensures that the number of samples you specify will be retained even when changing
the sample rate. If your external device connects to Live via an analog connection, you will want to
adjust your latency settings in milliseconds, which ensures that the amount of time you specify will be
retained when changing the sample rate. Note that adjusting in samples gives you finer control, so
even in cases when you’re working with analog devices, you may want to “fine tune“ your latency in
samples in order to achieve the lowest possible latency. In this case, be sure to switch back to
milliseconds before changing your sample rate. Any latency introduced by devices within Live will be
compensated for automatically, so the slider will be disabled when using the External Instrument
Device to route internally.

Note: If the Delay Compensation option is unchecked in the Options menu, the Hardware Latency
slider is disabled.

For more detailed information about routing scenarios with the External Instrument device, please see
the Routing and I/O chapter.

28.7 Impulse

The Impulse Instrument.

Impulse is a drum sampler with complex modulation capabilities. The eight drum samples loaded into
Impulse’s sample slots can be time-stretched, filtered and processed by envelope, saturation, pan and
volume components, nearly all of which are subject to random and velocity-based modulation.

28.7.1 Sample Slots

Drag and drop samples into any of Impulse’s sample slots from the browser or the Session and
Arrangement Views. Alternatively, each sample slot features a Hot-Swap button for hot-swapping
samples. Loaded samples can be deleted using the Backspace (Win) or Delete (Mac) key.

Imported samples are automatically mapped onto your MIDI keyboard, providing that it is plugged in
and acknowledged by Live. C3 on the keyboard will trigger the leftmost sample, and the other
samples will follow suit in the octave from C3 to C4. Impulse’s eight slots will appear labeled in the
MIDI Editor’s key tracks when the Fold button is active, even if the given key track is void of MIDI
notes. Mapping can be transposed from the default by applying a Pitch device, or it can be
rearranged by applying a Scale device.

Each of the eight samples has a proprietary set of parameters, located in the area below the sample
slots and visible when the sample is clicked. Adjustments to sample settings are only captured once
you hit a new note — they do not affect currently playing notes. Note that this behavior also defines
how Impulse reacts to parameter changes from clip envelopes or automation, which are applied once
a new note starts. If you want to achieve continuous changes as a note plays, you may want to use
the Simpler instrument.

Slot 8’s parameters also include a Link button, located in the lower left corner, which links slot 8 with
slot 7. Linking the two slots allows slot 7’s activation to stop slot 8’s playback, and vice versa. This was
designed with a specific situation in mind (but can, of course, be used for other purposes): Replicating
the way that closed hi-hats will silence open hi-hats.

Each slot can be played, soloed, muted or hot-swapped using controls that appear when the mouse
hovers over it.

28.7.2 Start, Transpose and Stretch

The Start control defines where Impulse begins playing a sample, and can be set up to 100 ms later
than the actual sample beginning. The Transp (Transpose) control adjusts the transposition of the
sample by +/- 48 semitones, and can be modulated by incoming note velocity or a random value, as
set in the appropriate fields.

The Stretch control has values from -100 to 100 percent. Negative values will shorten the sample, and
positive values will stretch it. Two different stretching algorithms are available: Mode A is ideal for low
sounds, such as toms or bass, while Mode B is better for high sounds, such as cymbals. The Stretch
value can also be modulated by MIDI note velocity.

28.7.3 Filter

The Filter section offers a broad range of filter types, each of which can impart different sonic
characteristics onto the sample by removing certain frequencies. The Frequency control defines where
in the harmonic spectrum the filter is applied; the Resonance control boosts frequencies near that
point. Filter Frequency can be modulated by either a random value or by MIDI note velocity.

28.7.4 Saturator and Envelope

The Saturator gives the sample a fatter, rounder, more analog sound, and can be switched on and off
as desired. The Drive control boosts the signal and adds distortion. Coincidentally, this makes most
signals much louder, and should usually be compensated for by lowering the sample’s volume
control. Extreme Drive settings on low-pitched sounds will produce the typical, overdriven analog
synth drum sounds.

The envelope can be adjusted using the Decay control, which can be set to a maximum of 10.0
seconds. Impulse has two decay modes: Trigger Mode allows the sample to decay with the note;
Gate Mode forces the envelope to wait for a Note Off message before beginning the decay. This
mode is useful in situations where you need variable decay lengths, as is the case with hi-hat cymbal
sounds.

28.7.5 Pan and Volume

Each sample has Volume and Pan controls that adjust amplitude and stereo positioning, respectively.
Both controls can be modulated: Pan by velocity and a random value, and Volume by velocity only.

28.7.6 Global Controls

The parameters located to the right of the sample slots are global controls that apply to all samples
within Impulse’s domain. Volume adjusts the overall level of the instrument, and Transp adjusts the
transposition of all samples. The Time control governs the time-stretching and decay of all samples,
allowing you to morph between short and stretched drum sounds.

28.7.7 Individual Outputs

When a new instance of Impulse is dragged into a track, its signal will be mixed with those of the other
instruments and effects feeding the audio chain of the track. It can oftentimes make more sense to
isolate the instrument or one of its individual drum samples, and send this signal to a separate track.
Please see the Routing and I/O chapter to learn how to accomplish this for Impulse’s overall signal or
for Impulse’s individual sample slots.

28.8 Meld

The Meld Instrument.

Meld is a versatile synthesizer that combines two independent macro oscillator engines into one
device. While it can quickly dial in classic analog-style patches, Meld’s character shines through in
the array of synthesis and filtering techniques it lets you layer and experiment with. Each of the
device’s engines has a dedicated filter, envelopes, LFOs, and a MIDI and MPE-enabled Modulation
Matrix, as well as two oscillator-dependent macro knobs that control parameters ranging from simple
overtone modulation to more unusual features like noise loop fragmentation, chiptone pulsewidth, and
raindrop generation density. Meld is designed to produce expressive, unfamiliar sounds guided by
musical intention rather than technical detail.

28.8.1 General Overview

Meld’s dual-layer architecture can use up to two polyphonic synth engines at once. Its interface is
divided into four main sections: the engines, the modulation section, the filters, and the global mix
controls. This modular-inspired configuration makes it easy to add texture and movement to your
sounds, but also to produce and capture musical surprises. To get familiar with some of Meld’s
possibilities, try combining different waveform types and playing with each engine’s modulation

macros. For more control, try mapping an engine’s parameters to its Modulation Matrix, or
automating the device’s macro knobs using an LFO device. The more you experiment with the
interaction between Meld’s two layers, the more you’ll make the device your own.

Meld can be expanded using the Toggle Expanded View button in the device header. When in
expanded view, all possible modulation targets and sources will be shown. The A and B toggles can
be used to switch between each engine. Parameter modulation values can be copied from one
engine to another using the Copy to A and Copy to B buttons. Clicking the X button will erase all
active modulation values.

Meld in Expanded View.

28.8.2 Oscillators

Meld’s Oscillators.

Meld’s two engines can be turned on or off independently via switches in the Engines section.
Deactivating one of Meld’s engines will deactivate its associated filter in the device’s Filters section. A
filter can be turned on or off without affecting the activation of the engine it’s linked to.

Each of Meld’s engines has three pitch controls (Octaves, Semitones, and Cents). When the Use
Current Scale toggle is activated, the semitone indicator (st) switches to scale degrees (sd). You can
use these pitch controls to add harmonic depth to your sound, for example by transposing an engine
up an octave or a fifth, or by subtly detuning it in cents.

Engines A and B each have a selection of twenty-four oscillator types to choose from, including six
scale aware oscillators marked with a (♭♯). These range from simple sine wave generation oscillators
to layered wave swarms, complex frequency modulation, noise looping, and ambient sound

generation algorithms. Oscillator Types can be selected from an engine’s drop-down menu or cycled
through using the arrows in the Oscillator Types displays.

28.8.3 Oscillator Macros

Meld’s Oscillator Macros.

Engines A and B each have two dedicated macro knobs, which change along with the oscillator type
selected. All four of the oscillator macro knobs can be assigned to a MIDI controller for live
performance or to the LFO device for automated modulation. They can also be modulated internally,
using the Modulation Matrix.

The Basic Shapes oscillator has two macro knobs, Shape and Tone. Shape morphs the oscillator’s
waveform between a sine, triangle, saw, and square wave. Tone changes the pulse width of the
source wave.

The Dual Basic Shapes oscillator has two macro knobs, Shape and Detune. Shape morphs the
oscillator’s waveform through sine, triangle, saw, and square wave shapes. Detune adds a copy of
this initial wave and detunes it.

The Noisy Shapes oscillator has two macro knobs, Shape and Rough. Shape morphs the oscillator’s
waveform through sine, triangle, saw, and square wave shapes. Rough adds noise distortion to this
source wave.

The Square Sync oscillator has two macro knobs, Freq 1 and Freq 2. These two controls change the
frequencies of the oscillator’s two synced square waves.

The Square 5th oscillator has two macro knobs, 5th Amt and P Width. 5th Amt morphs the oscillator’s
initial square wave to a second square wave that is a perfect fifth above it. P Width changes the pulse
width of the square wave being generated.

The Sub oscillator has two macro knobs, Tone and Aux. Tone morphs the oscillator’s initial sine wave
into a square wave. Aux adds a lower subharmonic sine wave to the initial sine wave being
generated.

The Swarm Sine, Swarm Triangle, Swarm Saw, and Swarm Square oscillators have two macro knobs,
Motion and Spacing. Motion adds modulation to the wave swarm being produced. Spacing fades
between increasingly complex chords as the amount applied is increased.

The Harmonic Fm oscillator has two macro knobs, Amount and Ratio, which change the modulation
amount and ratio in the frequency modulation algorithm.

The Fold Fm oscillator has two macro knobs, Amount and Shape. Amount changes the modulation
amount in the frequency modulation algorithm and Shape changes the shape of its carrier wave.

The Squelch oscillator has two macro knobs, Amount and Feedback. Amount changes the modulation
depth of the frequency modulation algorithm, and Feedback changes the amount of signal being fed
back into the device.

The Simple Fm oscillator has two macro knobs, Amount and Ratio, which change the modulation
amount and the depth in the frequency modulation algorithm, respectively.

The Chip oscillator has two macro knobs, Tone and Rate. Tone changes the oscillator’s pitch and pulse
width. Rate changes the speed of the chip interval being used.

The Shepard’s Pi oscillator has two macro knobs, Rate and Width. Rate changes the speed and
direction of the oscillator. Values 0.0 through 49.9 produce falling movements, and values 50.1
through 100.0 produce ascending movements. At 50.0, no movement is produced. Width changes
the number of octaves being used by the oscillator.

The Tarp oscillator has two macro knobs, Decay and Tone, which change the algorithm’s decay
amount and tonality.

The Extratone oscillator has two macro knobs, Pitch and Env Amount, which change the oscillator’s
pitch and envelope behavior.

The Noise Loop oscillator has two macro knobs, Rate and Fade. Rate sets the rate at which fragments
of different noise loops occur. At higher values, the oscillator produces noise. Fade dials in the grain
or roughness of the noise.

The Filtered Noise oscillator has two macro knobs, Freq and Width, which change the oscillator’s filter
frequency and width.

The Bitgrunge oscillator has two macro knobs, Freq and Mult. Freq adjusts the frequency of the square
wave being produced. Mult adjusts the number of sub-octaves being generated in relation to this
initial square wave. At its maximum setting, no sub-octaves are generated. At its minimum, a large
number of sub-octaves is generated.

The Crackle oscillator has two macro knobs, Density and Intensity. Density sets the average rate of
crackles being produced. Intensity adjusts the distribution of loudness and brightness within the
crackles.

The Rain oscillator has two macro knobs, Tone and Rate. Tone sets the resonance of the raindrop and
wind sounds being generated. This makes the oscillator tonal and dependent on the notes you play.
Rate sets the density of raindrop sounds being generated.

The Bubble oscillator has two macro knobs, Density and Spread. Density sets the rate of bubble
generation and Spread sets the randomness of the size of the bubbles being produced.

28.8.4 Envelopes Tab

Engine A’s Amplitude Envelope.

Each of Meld’s envelopes has Attack, Decay, Sustain, and Release controls. These can be adjusted by
sliding the numerical values at the bottom of the Envelope section up or down, entering a value using
your computer keyboard, or clicking and dragging the breakpoints on the envelope’s graphical
display.

Attack, Decay, and Release Slope controls are marked in red, and can be adjusted by sliding the
numerical values at the bottom of the section, entering a value using your computer keyboard, or
clicking and dragging the diamonds between the breakpoints in the Envelope section’s graphical
displays.

Amplitude and Modulation envelopes have three Envelope Loop Modes. In Trigger mode, all
segments of the envelope play once a note is received, while the selected Sustain level is ignored. In
Loop mode, the entire envelope is looped without holding the selected Sustain level. In AD Loop
mode, only the Attack and Decay portions of the envelope are looped.

The Modulation envelope has one additional set of parameters: the Initial, Peak, and Final levels.
These parameters set the position of the envelope when it is triggered and released, which offers more
flexibility for modulation.

Initial and Final Parameters in Engine B’s Modulation Envelope.

Activating the Link Envelopes button links each engine’s Amplitude and Modulation envelopes. This is
useful for having Meld’s two engines function as a single instrument.

28.8.5 LFOs Tab

Engine A’s LFOs.

Each of Meld’s engines has two dedicated LFOs. The rates of LFO 1 and LFO 2 can be set in Hertz or
tempo-synced, and a Phase Offset slider offsets each LFO’s phase. When Retrigger is enabled, the
LFO restarts at the position set by the Phase Offset slider.

LFO 1’s waveform can be selected from the LFO 1 Type drop-down menu, which provides six
waveform types to choose from: Basic Shapes, Ramp, Wander, Alternate, Euclid, and Pulsate. These
waveforms can be further shaped using the LFO’s Rate knob and the two macro knobs adjacent to it,
which change depending on the waveform type selected.

LFO 1 can also be modulated in the LFO 1 FX panel. The FX1 and FX2 drop-down menus each have
seventeen effect types that can be serially applied to LFO 1. The degree of the effect applied can be
changed via its corresponding macro knob. Note that LFO 1 and LFO1 FX can be used as
independent modulation sources in Meld’s Modulation Matrix.

LFO 2 provides six classic waveform types to choose from: Sine, Tri, Saw Up, Saw Down, Rectangle,
Random S&H. LFO 2 can be used as a third independent modulation source in Meld’s Modulation
Matrix.

28.8.6 Matrix Tab

Engine B’s Modulation Matrix.

Meld’s Modulation Matrix lets you assign modulation sources to modulation targets within the device.
For example, Engine A’s LFO 1 could be used to modulate its Volume, or Engine B’s Modulation
Envelope could be used to modulate its Filter Frequency.

Modulation sources are listed horizontally and modulation targets are listed vertically. Click and drag
a cell up or down to apply modulation between parameters. Negative values will make envelopes
and LFOs faster and positive values will make them slower. Note that some parameters have additive
modulation applied to them, while others have multiplicative modulation applied to them.

Click on a parameter to add it to the Modulation Matrix. Parameters are added to the Modulation
Matrix of the engine currently selected with the Display Selector Tab. If a parameter isn’t being
modulated, it will disappear from the Modulation Matrix when another parameter is clicked.

28.8.7 MIDI and MPE Tabs

Engine A’s MIDI Tab.

Meld’s MIDI and MPE tabs let you use MIDI and MPE functionality as modulation sources, which can
transform Meld into a dynamic performance tool.

When Velocity is set as a modulation source, Meld will use an incoming MIDI note’s velocity value to
modulate its modulation target for the duration of that note.

When Pitch is set as a modulation source, Meld will use an incoming MIDI note’s pitch value to
modulate its modulation target for the duration of that note.

When Random is set as a modulation source, Meld will modulate its modulation target by a random
value, which is calculated each time a note is triggered.

Pitch Bend, Press, and Modulation Wheel are hardware controls found on many MIDI controller
devices. Note Pitch Bend, Slide, and Press are hardware controls found on many MPE controller
devices. If you don’t have a MIDI or MPE controller, you can still modulate these parameters using
clip envelopes.

28.8.8 Settings Tab

Meld’s Engine Settings.

Meld’s Settings tab has three global settings that can be applied per engine: Osc Key Tracking, Scale
Awareness, and Glide.

The Osc Key Tracking switch activates or deactivates oscillator key tracking. When activated, an
oscillator will play the pitch of whatever incoming MIDI note it receives. When deactivated, an

oscillator will play a constant pitch of C3 for all incoming MIDI notes, or the root of a scale in the C3
octave if Scale Mode has been activated. This is useful for performing drones or percussive sounds,
for example.

Enabling the Phase Reset switch resets the phase of the oscillator to a consistent value with each new
note. The Phase Spread switch also becomes accessible when Phase Reset is enabled. When Phase
Spread is activated, the oscillator’s start phase is spread based on the Spread modulation source in
the Modulation Matrix. When Phase Spread is deactivated, the start phase is set to zero.

Two switches can be activated in the Scale Awareness section: Oscillator Scale Awareness and Filter
Scale Awareness.

When Oscillator Scale Awareness is activated, pitches controlled by scale-aware oscillator types will
also be in scale. The following oscillator types, marked with a (♭♯), are scale aware: Dual Basic
Shapes, Swarm Sine, Swarm Triangle, Swarm Saw, Swarm Square, and Chip.

When Filter Scale Awareness is enabled, the resonating frequencies of scale-aware filter types will
also be in scale. The following filter types, marked with a (♭♯), are scale aware: Plate Resonator and
Membrane Resonator.

The Glide section has two glide modes, Portamento (Porta) and Glissando (Gliss), as well as a Glide
Time control.

The Glide Time control sets the time that overlapping notes take to slide into the next incoming pitch.
Glide is active in both Mono and Poly modes.

When Portamento is activated and a note is played while another is held down, the first note’s pitch
will slide progressively into the second note’s pitch. When Glissando is activated and a note is played
while another is held down, the first note’s pitch will ascend or descend into the second note’s pitch in
discrete steps. Glissando produces these steps in scale degrees if scale awareness is enabled. Note
that portamento and glissando effects are only audible when Glide Time is set to a value above zero.

28.8.9 Filters

Meld’s Filters Section.

Meld’s two engines each have a dedicated filter, A and B, which can be turned on or off
independently via switches in the Filters section.

The Filter Frequency knob sets the center of the filter’s cutoff frequency.

The Filter Type drop-down menu lets you choose from seventeen different filter types. Each filter has
two macro knobs, which change with the filter type selected.

The most common filter macro knobs in Meld are Q and Drive. Q adjusts the emphasis of the
frequencies around a filter’s cutoff frequency. Drive applies saturation to the input signal before it
passes through the filter, which is useful for producing distortion.

The SVF 12dB and 24dB filters are state variable filters. The L-B-H-N macro control morphs through
this filter type’s four possible configurations: low-pass, band-pass, high-pass, and notch.

The MS2 filters are modeled on a Sallen-Key design from a famous semi-modular Japanese
monosynth, which applies soft clipping to limit resonance. They are available in low-pass and high-
pass configurations in Meld.

The OSR filter is modeled on a state variable filter from a rare British monosynth whose resonance is
limited by a unique hard-clipping diode. It is available in a band-pass configuration in Meld.

LP Crunch 12dB is a dual-mode low-pass filter that feeds the distortion it produces back into itself.

The LP Switched Res filter is modeled on low-pass filters whose resistors are replaced with fast switches
to produce downsampling artifacts. The Lofi macro knob changes the frequency of the filter’s resistors.
If set to a high value, the filter produces a more crushed sound. If set to a low value, it produces a
smoother sound.

Filther is modeled on a low-pass filter that applies distortion to a signal’s input and output. It uses a
hard diode clipper on the input signal and soft saturation on the output signal.

The Eq Peak and Eq Notch filters are peak and notch filters that apply gain and width to an input
signal. The Eq Peak filter’s Boost macro knob boosts frequencies around the filter’s cutoff point. The Eq
Notch filter’s Cut macro knob cuts frequencies around the filter’s cutoff point.

The Phaser filter is a six-stage delayless inverted feedback phaser with variable feedback and notch
spacing. The Phaser filter’s Feedback macro knob sets the amount of output being fed back into the
filter’s input. The Spread macro knob adjusts the spacing between the filter’s notches in the frequency
spectrum.

The Redux filter is a resampler and bitcrusher with a variable sample rate, quantization, and knob
over the amount of resampling artifacts it produces. The Crush macro knob sets the bit depth of the
filter’s output. The Lofi macro knob adjusts the mix between a filtered, sample rate-reduced version of
the signal and the unfiltered, downsampled artifacts Redux has produced.

The Vowel filter is a formant filter that mimics the characteristics of vowels being pronounced, with
various configurations that can be morphed through using the filter’s Morph macro knob.

The Comb + and Comb - filters are feedforward and feedback filters. The Feedback macro knob
adjusts the amount of feedforward or feedback being sent from the filter’s delayed output back into its
input. The Damp knob applies a low-pass filter to the filter’s output, to damp high frequencies.

The Plate Resonator filter applies a set of modal resonators tuned to the first 32 modes of a
rectangular plate to the input signal. The plate’s size, resonance, and dimension ratio can be modified

using its macro knobs. When Filter Scale Awareness is enabled, this filter’s resonating frequencies will
be in scale.

The Membrane Resonator filter applies a set of modal resonators tuned to the first 32 modes of a
circular membrane to the input signal. The membrane’s size, resonance, and high frequency damping
can be modified using its macro knobs. When Filter Scale Awareness is enabled, this filter’s resonating
frequencies will be in scale.

28.8.10 Mix Section

Mix Controls for Each Engine.

Each of Meld’s engines has Volume and Pan controls, as well as a dedicated Tone Filter that can be
found in Meld’s Mix section. The Volume control adjusts the overall output of an engine, and the Pan
control adjusts its position in the stereo field.

Meld’s Tone Filter control functions like a combined high and low-pass filter. When set to positive
values, it reduces an engine’s low frequencies. When set to negative values, it reduces an engine’s
high frequencies.

Meld’s built-in limiter can be activated by clicking the Limit button. When activated, the limiter is
applied per voice, after both engines have been mixed and the global Drive setting has been
applied. This is helpful for controlling Meld’s overall output level when both engines are in use.

28.8.11 Global Controls

Meld’s Global Parameters.

Meld’s global controls affect the overall sound and behavior of the instrument.

Meld’s Mono/Poly switch toggles between a monophonic and polyphonic output.

When Mono is activated, the Legato switch can be toggled on or off. When Legato is activated, if a
new note is played while another is held, the new note will use the original note’s envelope from its

current position. When Legato is deactivated, each new note played will trigger its own envelope
from the beginning.

When Poly is activated, a drop-down menu lets you set the number of voices usable by Meld, from 2
to 12.

The Spread control adjusts the range of the Spread modulation source in Meld’s Modulation Matrix.
When a voice number is set in the Stacked Voices control, Spread produces an offset between each
stacked voice. When Stacked Voices is set to Off, Spread produces a range of different values for
each note in a held chord. Note that Spread will have no effect if not applied to a modulation target
in the Modulation Matrix.

The Stacked Voices drop-down menu adjusts the number of stacked voices for a single note. Stacked
voices duplicate both engines for each note (including filters, modulation, and mixer settings), and
can create a heavy CPU load.

The Mixer Drive control sets the amount of saturation applied to Meld’s output. Drive is applied per
voice, after mixer settings, and before the limiter.

The Volume control adjusts Meld’s output volume.

The Use Current Scale button makes Meld follow Live’s Scale Mode. When activated, Meld’s
oscillators follow Live’s current scale, with all transpositions (including the Pitch Quant modulation
target in the Modulation Matrix) occurring in scale degrees rather than semitones.

28.9 Operator

The Operator Instrument.

Operator is an advanced and flexible synthesizer that combines the concept of “frequency
modulation“ (FM) with classic subtractive and additive synthesis. It uses four multi-waveform
oscillators that can modulate each other’s frequencies, creating very complex timbres from a limited
number of objects. Operator includes a filter section, an LFO and global controls, as well as individual
envelopes for the oscillators, filter, LFO and pitch.

28.9.1 General Overview

The interface of Operator consists of two parts: the display surrounded on either side by the shell. The
shell offers the most important parameters in a single view and is divided into eight sections. On the
left side, you will find four oscillator sections, and on the right side from top to bottom, the LFO, the
filter section, the pitch section and the global parameters. If you change one of the shell parameters,
the display in the center will automatically show the details of the relevant section. When creating your
own sounds, for example, you can conveniently access the level and frequency of all oscillators at
once via the shell, and then adjust each individual oscillator’s envelope, waveform and other
parameters in its display.

Operator can be folded with the triangular button at its upper left. This is convenient if you do not
need to access the display details.

Operator Folded.

Each of Operator’s oscillators can either output its signal directly or use its signal to modulate another
oscillator. Operator offers eleven predefined algorithms that determine how the oscillators are
connected. An algorithm is chosen by clicking on one of the structure icons in the global display,
which will appear if the bottom right (global) section of the shell is selected. Signals will flow from top
to bottom between the oscillators shown in an algorithm icon. The algorithm selector can be mapped
to a MIDI controller, automated, or modulated in real time, just like any other parameter.

Operator’s Algorithms.

Typically, FM synthesis makes use of pure sine waves, creating more complex waveforms via
modulation. However, in order to simplify sound design and to create a wider range of possible
sounds, we designed Operator to produce a variety of other waveforms, including two types of noise.

You can also draw your own waveforms via a partial editor. The instrument is made complete with an
LFO, a pitch envelope and a filter section. Note that lots of “classic“ FM synthesizers create fantastic
sounds without using filters at all, so we suggest exploring the possibilities of FM without the filter at
first, and adding it later if necessary.

Operator will keep you busy if you want to dive deep into sound design! If you want to break the
universe apart completely and reassemble it, you should also try modulating Operator’s controls with
clip envelopes or track automation.

28.9.2 Oscillator Section

Oscillator A’s Display and Shell Parameters.

28.9.2.1 Built-in Waveforms

The oscillators come with a built-in collection of basic waveform types — sine, sawtooth, square,
triangle and noise — which are selected from the Wave chooser in the individual oscillator displays.
The first of these waveforms is a pure, mathematical sine wave, which is usually the first choice for
many FM timbres. We also added “Sine 4 Bit“ and “Sine 8 Bit“ to provide the retro sound adored by
C64 fans, and “Saw D“ and “Square D“ digital waveforms, which are especially good for digital
bass sounds. The square, triangle and sawtooth waveforms are resynthesized approximations of the
ideal shape. The numbers included in the displayed name (e.g., “Square 6“) define how many
harmonics are used for the resynthesis. Lower numbers sound mellower and are less likely to create
aliasing when used on high pitches. There are also two built-in noise waveforms. The first, “Noise
Looped,“ is a looping sample of noise. For truly random noise, choose “Noise White.“

28.9.2.2 User Waveforms

The “User“ entry in the Wave chooser allows you to create your own waveforms by drawing the
amplitudes of the oscillator’s harmonics. You can also select one of the built-in waveforms and then
edit it in the same way. The small display next to the Wave chooser gives a real-time overview of your
waveform.

When your mouse is over the Oscillator display area, the cursor will change to a pencil. Drawing in
the display area then raises or lowers the amplitudes of the harmonics. As you adjust the amplitudes,
the Status Bar will show the number of the harmonic you’re adjusting as well as its amplitude. Holding

Shift and dragging will constrain horizontal mouse movement, allowing you to adjust the
amplitude of only one harmonic at a time.

You can switch between editing the first 16, 32 or 64 harmonics via the switches to the right of the
display. Higher harmonics can be generated by repeating the drawn partials with a gradual fadeout,
based on the settings in the Repeat chooser. Low Repeat values result in a brighter sound, while higher
values result in more high-end roll-off and a more prominent fundamental. With Repeat off, partials
above the 16th, 32nd or 64th harmonic are truncated.

The context menu in the harmonics display offers options for editing only the even or odd harmonics.
This is set to “All“ by default. The context menu also offers an option to toggle Normalize on or off.
When enabled, the oscillator’s overall output level is maintained as you draw additional harmonics.
When disabled, additional harmonics add additional level. Note that the volume can become
extremely loud if Normalize is off.

You can export your waveform in .ams format to the Samples/Waveforms folder in your User Library
via an option in the context menu. Ams files can be imported back into Operator by dragging them
from the browser onto one of the oscillator’s display areas. Ams files can also be loaded into Simpler
or Sampler.

Both the built-in and user waveforms can be copied and pasted from one oscillator to another using
the Osc Preview’s context menu.

28.9.2.3 More Oscillator Parameters

The frequency of an oscillator can be adjusted in the shell with its Coarse and Fine controls. An
oscillator’s frequency usually follows that of played notes, but for some sounds it might be useful to set
one or more oscillators to fixed frequencies. This can be done for each individual oscillator by
activating the Fixed option. This allows the creation of sounds in which only the timbre will vary when
different notes are played, but the tuning will stay the same. Fixed Mode would be useful, for
example, in creating live drum sounds. Fixed Mode also allows producing very low frequencies down
to 0.1 Hz. Note that when Fixed Mode is active, the frequency of the oscillator is controlled in the shell
with the Frequency (Freq) and Multiplier (Multi) controls.

Operator includes a special Osc < Vel control for each oscillator that allows altering frequency as a
function of velocity. This feature can be very useful when working with sequenced sounds in which the
velocity of each note can be adjusted carefully. Part of this functionality is the adjacent Q (Quantize)
button. If this control is activated, the frequency will only move in whole numbers, just as if the Coarse
control were being manually adjusted. If quantize is not activated, the frequency will be shifted in an
unquantized manner, leading to detuned or inharmonic sounds (which very well could be exactly
what you want…).

The amplitude of an oscillator depends on the Level setting of the oscillator in the shell and on its
envelope, which is shown and edited when the Envelope display is visible. The envelopes can also be
modified by note velocity and note pitch with the Vel and Key parameters available in the Envelope
section of each oscillator’s display.

The phase of each oscillator can be adjusted using the Phase control in its display. With the R
(Retrigger) button enabled, the waveform restarts at the same position in its phase each time a note is
triggered. With R disabled, the oscillator is free-running.

As explained earlier oscillators can modulate each other when set up to do so with the global
display’s algorithms. When an oscillator is modulating another oscillator, two main properties define
the result: the amplitude of the modulating oscillator and the frequency ratio between both oscillators.
Any oscillator that is not modulated by another oscillator can modulate itself, via the Feedback
parameter in its display.

28.9.2.4 Aliasing

Aliasing distortion is a common side effect of all digital synthesis and is the result of the finite sample
rate and precision of digital systems. It mostly occurs at high frequencies. FM synthesis is especially
likely to produce this kind of effect, since one can easily create sounds with lots of high harmonics. This
also means that more complex oscillator waveforms, such as “Saw 32,“ tend to be more sensitive to
aliasing than pure sine waves. Aliasing is a two-fold beast: A bit of it can be exactly what is needed
to create a cool sound, yet a bit too much can make the timbre unplayable, as the perception of pitch
is lost when high notes suddenly fold back into arbitrary pitches. Operator minimizes aliasing by
working in a high-quality Antialias mode. This is on by default for new patches, but can be turned off
in the global section. The Tone parameter in the global section also allows for controlling aliasing. Its
effect is sometimes similar to a low-pass filter, but this depends on the nature of the sound itself and
cannot generally be predicted. If you want to familiarize yourself with the sound of aliasing, turn Tone
up fully and play a few very high notes. You will most likely notice that some notes sound completely
different from other notes. Now, turn Tone down and the effect will be reduced, but the sound will be
less bright.

28.9.3 LFO Section

Operator’s LFO Display and Shell Parameters.

The LFO in Operator can practically be thought of as a fifth oscillator. It runs at audio rates, and it
modulates the frequency of the other oscillators. It is possible to switch LFO modulation on or off for
each individual oscillator (and the filter) using the Dest. A buttons in the LFO’s display. The intensity of
the LFO’s modulation of these targets can be adjusted by the Dest. A slider. The LFO can also be
turned off entirely if it is unused.

The Dest. B chooser allows the LFO to modulate an additional parameter. The intensity of this
modulation is determined by the Dest. B slider.

The LFO offers a choice of classic LFO waveforms, sample and hold (S&H), and noise. Sample and
hold uses random numbers chosen at the rate of the LFO, creating the random steps useful for typical
retro-futuristic sci-fi sounds. The noise waveform is simply band-pass filtered noise.

Tip: FM synthesis can be used to create fantastic percussion sounds, and using the LFO with the noise
waveform is the key to great hi-hats and snares.

The frequency of the LFO is determined by the LFO Rate control in the shell, as well as the low/high/
sync setting of the adjacent LFO Range chooser. The frequency of the LFO can follow note pitch, be
fixed or be set to something in between. This is defined by the Rate < Key parameter in the LFO’s
display. With the R (Retrigger) button enabled, the LFO restarts at the same position in its phase each
time a note is triggered. With R disabled, the LFO is free-running.

The overall intensity of the LFO is set by the LFO Amount control in the shell. This parameter scales both
the Dest. A and B amounts and can be modulated by note velocity via the display’s Amt < Vel control.
The LFO’s intensity is also affected by its envelope.

28.9.4 Envelopes

Operator’s Oscillator B Envelope.

Operator has seven envelopes: one for each oscillator, a filter envelope, a pitch envelope and an
envelope for the LFO. All envelopes feature some special looping modes. Additionally, the filter and
pitch envelopes have adjustable slopes.

Each oscillator’s volume envelope is defined by six parameters: three rates and three levels. A rate is
the time it takes to go from one level to the next. For instance, a typical pad sound starts with the initial
level “-inf dB“ (which is silence), moves with an attack rate to its peak level, moves from there to the
sustain level with a decay rate, and then finally, after Note Off occurs, back to “-inf dB“ at the release
rate. Operator’s display provides a good overview of the actual shape of any particular envelope
and lets you directly adjust the curve by clicking on a breakpoint and dragging. The breakpoints
retain their selection after clicking, allowing them to be adjusted with the keyboard’s cursor keys, if
desired.

Envelope shapes can be copied and pasted from one oscillator to another in Operator using the
Envelope Display’s context menu.

As mentioned above, the filter and pitch envelopes also have adjustable slopes. Clicking on the
diamonds between the breakpoints allows you to adjust the slope of the envelope segments. Positive
slope values cause the envelope to move quickly at the beginning, then slower. Negative slope values
cause the envelope to remain flat for longer, then move faster at the end. A slope of zero is linear; the
envelope will move at the same rate throughout the segment.

With FM synthesis, it is possible to create spectacular, endless, permuting sounds; the key to doing this
is looping envelopes. Loop Mode can be activated in the lower left corner of the display. If an
envelope in Operator is in Loop Mode and reaches sustain level while the note is still being held, it
will be retriggered. The rate for this movement is defined by the Loop Time parameter. Note that
envelopes in Loop Mode can loop very quickly and can therefore be used to achieve effects that one
would not normally expect from an envelope generator.

While Loop Mode is good for textures and experimental sounds, Operator also includes Beat and
Sync Modes, which provide a simple way of creating rhythmical sounds. If set to Beat Mode, an
envelope will restart after the beat time selected from the Repeat chooser. In Beat Mode, the repeat
time is defined in fractions of song time, but notes are not quantized. If you play a note a bit out of
sync, it will repeat perfectly but stay out of sync. In Sync Mode however, the first repetition is
quantized to the nearest 16th note and, as a result, all following repetitions are synced to the song
tempo. Note that Sync Mode only works if the song is playing, and otherwise it will behave like Beat
Mode.

To avoid the audible clicks caused by restarting from its initial level, a looped envelope will restart
from its actual level and move with the set attack rate to peak level.

There is also a mode called Trigger that is ideal for working with percussive sounds. In this mode, Note
Off is ignored. This means that the length of time a key is held has no effect on the length of the sound.

The rates of all the envelopes in Operator can be scaled in unison by the Time control in the global
section of the shell. Note that beat-time values in Beat and Sync Modes are not influenced by the
global Time parameter. Envelope rates can be further modified by note pitch, as dictated by the Time
< Key parameter in the global section’s display. The rate of an individual envelope can also be
modified by velocity using the Time < Vel parameter. These modulations in conjunction with the loop
feature can be used to create very, very complex things…

The pitch envelope can be turned on or off for each individual oscillator and for the LFO using the
Destination A-D and LFO buttons in its display. The intensity of this envelope’s modulation of these
targets can be adjusted by the Dest. A slider and the envelope can be turned off altogether via the
switch in the pitch section of the shell.

Like the LFO, the pitch envelope can modulate an additional parameter as chosen by the Dest. B
chooser. The intensity of this modulation is determined by the Amt. B slider and the main Pitch Env
value.

The pitch and filter envelopes each have an additional parameter called End, which determines the
level the envelope will move to after the key is released. The rate of this envelope segment is
determined by the release time.

Tip: If the pitch envelope is only applied to the LFO and is looping, it can serve as another LFO,
modulating the rate of the first. And, since the envelope of the LFO itself can loop, it can serve as a
third LFO modulating the intensity of the first!

28.9.5 Filter Section

Operator’s Filter Display and Shell Parameters.

Operator’s filters can be very useful for modifying the sonically rich timbres created by the oscillators.
And, since the oscillators also provide you with the classic waveforms of analog synthesizers, you can
very easily build a subtractive synthesizer with them.

Operator offers a variety of filter types including low-pass, high-pass, band-pass, notch, and a
special Morph filter. Each filter can be switched between 12 and 24 dB slopes as well as a selection
of analog-modeled circuit behaviors developed in conjunction with Cytomic that emulate hardware
filters found on some classic analog synthesizers.

The Clean circuit option is a high-quality, CPU-efficient design that is the same as the filters used in EQ
Eight. This is available for all of the filter types.

The OSR circuit option is a state-variable type with resonance limited by a unique hard-clipping
diode. This is modeled on the filters used in a somewhat rare British monosynth, and is available for all
filter types.

The MS2 circuit option uses a Sallen-Key design and soft clipping to limit resonance. It is modeled on
the filters used in a famous semi-modular Japanese monosynth and is available for the low-pass and
high-pass filters.

The SMP circuit is a custom design not based on any particular hardware. It shares characteristics of
both the MS2 and PRD circuits and is available for the low-pass and high-pass filters.

The PRD circuit uses a ladder design and has no explicit resonance limiting. It is modeled on the filters
used in a legacy dual-oscillator monosynth from the United States and is available for the low-pass
and high-pass filters.

The most important filter parameters are the typical synth controls Frequency and Resonance.
Frequency determines where in the harmonic spectrum the filter is applied; Resonance boosts
frequencies near that point.

When using the low-pass, high-pass, or band-pass filter with any circuit type besides Clean, there is
an additional Drive control that can be used to add gain or distortion to the signal before it enters the
filter.

The Morph filter has an additional Morph control which sweeps the filter type continuously from low-
pass to band-pass to high-pass to notch and back to low-pass.

You can quickly snap the Morph control to a low-pass, band-pass, high-pass, or notch setting via
dedicated options in the context menu of the Morph slider.

The Envelope and Filter buttons in the filter section’s display area toggle between showing the filter
envelope and its frequency response. Filter cutoff frequency and resonance can be adjusted in the
shell or by dragging the filter response curve in the display area. Filter frequency can also be
modulated by the following:

•
•
•
•

Note velocity, via the Freq < Vel control in the filter’s display.
Note pitch, via the Freq < Key control in the filter’s display.
Filter envelope, via the Envelope control in the filter’s display.
LFO, done either by enabling the Dest. A “FIL“ switch in the LFO’s display, or by setting Dest. B
to Filter Freq.

The context menu for the Frequency knob contains an entry called “Play by Key.“ This automatically
configures the filter for optimal key tracking by setting Freq < Key to 100% and setting the cutoff to
466 Hz.

The filter’s signal can be routed through a waveshaper, whose curve type can be selected via the
Shaper chooser. The Shaper Drive (Shp. Drive) slider boosts or attenuates the signal level being sent
to the waveshaper, while the overall balance between the dry and processed signals can be adjusted
with the Dry/Wet control. With this set to 0%, the shaper and shaper drive parameters are bypassed.

28.9.6 Global Controls

Operator’s Global Display and Shell Parameters.

The global section contains parameters that affect Operator’s overall behavior. Additionally, the
global display area provides a comprehensive set of modulation routing controls.

The maximum number of Operator voices (notes) playing simultaneously can be adjusted with the
Voices parameter in the global display. Ideally, one would want to leave this setting high enough so

that no voices would be turned off while playing, however a setting between 6 and 12 is usually more
realistic when considering CPU power.

Tip: Some sounds should play monophonically by nature, which means that they should only use a
single voice. A flute is a good example. In these cases, you can set Voices to 1. If Voices is set to 1,
another effect occurs: Overlapping voices will be played legato, which means that the envelopes will
not be retriggered from voice to voice, and only pitch will change.

A global Volume control for the instrument can be found in the global section of the shell, and a Pan
control is located in the global section’s display. Pan can be modulated by note pitch or a random
factor, using the adjacent Pan < Key and Pan < Rnd controls, respectively.

The center of the global display allows for a wide variety of internal MIDI mappings. The MIDI
controllers Velocity, Key, Aftertouch, Pitch Bend and Mod Wheel can be mapped to two destinations
each, with independent modulation intensities set via the Amount sliders. Note that Time < Key and
pitch bend range have fixed assignments, although both modulation sources can still be routed to an
additional target. For more information about the available modulation options, see the complete
parameter list.

28.9.7 Glide and Spread

Operator’s Pitch Display and Shell Parameters.

Operator includes a polyphonic glide function. When this function is activated, new notes will start
with the pitch of the last note played and then slide gradually to their own played pitch. Glide can be
turned on or off and adjusted with the Glide Time control in the pitch display.

Operator also offers a special Spread parameter that creates a rich stereo chorus by using two voices
per note and panning one to the left and one to the right. The two voices are detuned, and the amount
of detuning can be adjusted with the Spread control in the pitch section of the shell.

Whether or not spread is applied to a particular note depends upon the setting of the Spread
parameter during the Note On event. To achieve special effects, you could, for instance, create a
sequence where Spread is 0 most of the time and turned on only for some notes. These notes will then
play in stereo, while the others will play mono. Note that Spread is a CPU-intensive parameter.

The pitch section also contains a global Transpose knob.

28.9.8 Strategies for Saving CPU Power

If you want to save CPU power, turn off features that you do not need or reduce the number of voices.
Specifically, turning off the filter or the LFO if they do not contribute to the sound will save CPU power.

For the sake of saving CPU resources, you will also usually want to reduce the number of voices to
something between 6 and 12, and carefully use the Spread feature. The Interpolation and Antialias
modes in the global display can also be turned off to conserve CPU resources.

Note that turning off the oscillators will not save CPU power.

28.9.9 Finally…

Operator is the result of an intense preoccupation with FM synthesis and a love and dedication to the
old hardware FM synthesizers, such as the Yamaha SY77, the Yamaha TX81Z and the NED Synclavier
II. FM synthesis was first explored musically by the composer and computer music pioneer John
Chowning in the mid-1960s. In 1973, he and Stanford University began a relationship with Yamaha
that lead to one of the most successful commercial musical instruments ever, the DX7.

John Chowning realized some very amazing and beautiful musical pieces based on a synthesis
concept that you can now explore yourself simply by playing with Operator in Live.

We wish you loads of fun with it!

28.9.10 The Complete Parameter List

The function of each Operator parameter is explained in the forthcoming sections. Remember that you
can also access explanations of controls in Live (including those belonging to Operator) directly from
the software by placing the mouse over the control and reading the text that appears in the Info View.
Parameters in this list are grouped into sections based on where they appear in Operator.

28.9.10.1 Global Shell and Display

Time — This is a global control for all envelope rates.

Tone — Operator is capable of producing timbres with very high frequencies, which can sometimes
lead to aliasing artifacts. The Tone setting controls the high frequency content of sounds. Higher
settings are typically brighter but also more likely to produce aliasing.

Volume — This sets the overall volume of the instrument.

Algorithm — An oscillator can modulate other oscillators, be modulated by other oscillators, or both.
The algorithm defines the connections between the oscillators and therefore has a significant impact
on the sound that is created.

Voices — This sets the maximum number of notes that can sound simultaneously. If more notes than
available voices are requested, the oldest notes will be cut off.

Retrigger (R) — When enabled, notes that are enabled will be retriggered, rather than generating an
additional voice.

Interpolation — This toggles the interpolation algorithm of the oscillators and the LFO. If turned off,
some timbres will sound more rough, especially the noise waveform. Turning this off will also save
some CPU power.

Antialias — This toggles Operator’s high-quality antialias mode, which helps to minimize high-
frequency distortion. Disabling this modes reduces the CPU load.

Time < Key — The rates of all envelopes can be controlled by note pitch. If the global Time < Key
parameter is set to higher values, the envelopes run faster when higher notes are played.

Pitch Bend Range (PB Range) — This defines the effect of MIDI pitch bend messages.

Pan — Use this to adjust the panorama of each note. This is especially useful when modulated with
clip envelopes.

Pan < Key (Key) — If Pan < Key is set to higher values, low notes will pan relatively more to the left
channel, and higher notes to the right. Typically this is used for piano-like sounds.

Pan < Random (Rnd) — This defines the extent to which notes are randomly distributed between the
left and right channels.

28.9.10.2 Modulation Targets

These modulation targets are available as MIDI routing destinations in the global display, and also as
modulation targets for the LFO and pitch envelope.

Off — Disabled this controller’s modulation routing.

OSC Volume A-D — Modulates the volume of the selected oscillator.

OSC Crossfade A/C — Crossfades the volumes of the A and C oscillators based on the value of the
modulation source.

OSC Crossfade B/D — Crossfades the volumes of the B and D oscillators based on the value of the
modulation source.

OSC Feedback — Modulates the amount of feedback for all oscillators. Note that feedback is only
applied to oscillators that are not modulated by other oscillators.

OSC Fixed Frequency — Modulates the pitch of all oscillators that are in Fixed Frequency mode.

FM Drive — Modulates the volume of all oscillators which are modulating other oscillators, thus
changing the timbre.

Filter Frequency — Modulates the cutoff frequency of the filter.

Filter Q (Legacy) — Modulates the resonance of the filter when using the legacy filter types.

Filter Res — Modulates the resonance of the filter when using the updated filter types.

Filter Morph — Modulates the position in the filter’s morph cycle (only has an effect for the Morph
filter type.)

Filter Drive — Modulates the amount of the Drive (not available when the Morph filter is selected.)

Filter Envelope Amount — Modulates the filter’s envelope intensity.

Shaper Drive — Modulates the amount of gain applied to the filter’s waveshaper.

LFO Rate — Modulates the rate of the LFO.

LFO Amount — Modulates the intensity of the LFO.

Pitch Envelope Amount — Modulates the intensity of the pitch envelope.

Volume — Modulates Operator’s global output volume.

Panorama — Modulates the position of Operator’s output in the stereo field.

Tone — Modulates the global Tone parameter.

Time — Modulates the global control for all envelope rates.

28.9.10.3 Pitch Shell and Display

Pitch Envelope On — This turns the pitch envelope on and off. Turning it off if it is unused saves some
CPU power.

Pitch Envelope Amount (Pitch Env) — This sets the overall intensity of the pitch envelope. A value of
100% means that the pitch change is exactly defined by the pitch envelope’s levels. A value of -100%
inverts the sign of the pitch envelope levels.

Spread — If Spread is turned up, the synthesizer uses two detuned voices per note, one each on the
left and right stereo channels, to create chorusing sounds. Spread is a very CPU-intensive effect.

Transpose — This is the global transposition setting for the instrument. Changing this parameter will
affect notes that are already playing.

Pitch Envelope Rates < Velocity (Time < Vel) — This parameter exists for filter, pitch, LFO and volume
envelopes. It is therefore listed in the section on envelopes.

Glide (G) — With Glide on, notes will slide from the pitch of the last played note to their played pitch.
Note that all envelopes are not retriggered in this case if notes are being played legato.

Glide Time (Time) — This is the time it takes for a note to slide from the pitch of the last played note to
its final pitch when Glide is activated. This setting has no effect if Glide is not activated.

Pitch Envelope to Osc (Destination A-D) — The pitch envelope affects the frequency of the respective
oscillator if this is turned on.

Pitch Envelope to LFO (Destination LFO) — The pitch envelope affects the frequency of the LFO if this is
turned on.

Pitch Envelope Amount A — This sets the intensity of the pitch envelope’s modulation of the oscillators
and LFO.

Pitch Envelope Destination B — This sets the second modulation destination for the pitch envelope.

Pitch Envelope Amount B — This sets the intensity of the pitch envelope’s modulation of the secondary
target.

28.9.10.4 Filter Shell and Display

Filter On — This turns the filter on and off. Turning it off when it is unused saves CPU power.

Filter Type — This chooser selects from low-pass, high-pass, band-pass, notch, and Morph filters.

Circuit Type — This chooser selects from a variety of circuit types that emulate the character of classic
analog synthesizers.

Filter Frequency (Freq) — This defines the center or cutoff frequency of the filter. Note that the resulting
frequency may also be modulated by note velocity and by the filter envelope.

Filter Resonance (Res) — This defines the resonance around the filter frequency of the low-pass and
high-pass filters, and the width of the band-pass and notch filters.

Envelope / Filter Switches — These switches toggle the display between the filter’s envelope and its
frequency response.

Filter Frequency < Velocity (Freq < Vel) — Filter frequency is modulated by note velocity according to
this setting.

Filter Frequency < Key (Freq < Key) — Filter frequency is modulated by note pitch according to this
setting. A value of 100% means that the frequency doubles per octave. The center point for this
function is C3.

Filter Envelope Rates < Velocity (Time < Vel) — This parameter exists for filter, pitch, LFO and volume
envelopes. It is therefore listed in the section on envelopes.

Filter Frequency < Envelope (Envelope) — Filter frequency is modulated by the filter envelope
according to this setting. A value of 100% means that the envelope can create a maximum frequency
shift of approximately 9 octaves.

Filter Drive (Flt. Drive) — Applies additional input gain to the signal before it enters the filter.

Morph — Controls the position of the Morph filter in its morph cycle.

Shaper — This chooser selects the curve for the filter’s waveshaper.

Shaper Drive (Shp. Drive) — This boosts or attenuates the signal level being sent to the waveshaper.

Dry/Wet — This adjusts the balance between the dry signal and the signal processed by the
waveshaper.

28.9.10.5 LFO Shell and Display

LFO On — This turns the LFO (low-frequency oscillator) on and off. Turning it off when it is unused
saves some CPU power.

LFO Waveform — Select from among several typical LFO waveforms. Sample and Hold (S&H)
creates random steps, and Noise supplies band-pass filtered noise. All waveforms are band-limited to
avoid unwanted clicks.

LFO Range — The LFO covers an extreme frequency range. Choose Low for a range from 50 seconds
to 30 Hz, or Hi for 8 Hz to 12 kHz. Sync causes the LFO’s rate to be synced to your Set’s tempo. Due
to the possible high frequencies, the LFO can also function as a fifth oscillator.

Retrigger (R) — When enabled, the LFO restarts at the same position in its phase each time a note is
triggered. With R disabled, the LFO is free-running.

LFO Rate (Rate) — This sets the rate of the LFO. The actual frequency also depends on the setting of
the LFO Range and the LFO Rate < Key controls.

LFO Amount (Amount) — This sets the overall intensity of the LFO. Note that the actual effect also
depends on the LFO envelope.

LFO to Osc (Destination A-D) — The LFO modulates the frequency of the respective oscillator if this is
turned on.

LFO to Filter Cutoff Frequency (Destination FIL) — The LFO modulates the cutoff frequency of the filter if
this is turned on.

LFO Amount A — This sets the intensity of the LFO’s modulation of the oscillators and filter.

LFO Destination B — This sets the second modulation destination for the LFO.

LFO Amount B — This sets the intensity of the LFO’s modulation of the secondary target.

LFO Envelope Rates < Velocity (Time < Vel) — This parameter exists for filter, pitch, LFO and volume
envelopes. It is therefore listed in the section on envelopes.

LFO Rate < Key (Rate < Key) — The LFO’s frequency can be a function of note pitch. If this is set to
100%, the LFO will double its frequency per octave, functioning like a normal oscillator.

LFO Amount < Velocity (Amt < Vel) — This setting adjusts modulation of the LFO intensity by note
velocity.

28.9.10.6 Oscillators A-D Shell and Display

Osc On — This turns the oscillator on and off.

Osc Coarse Frequency (Coarse) — The relationship between oscillator frequency and note pitch is
defined by the Coarse and Fine parameters. Coarse sets the ratio in whole numbers, creating a
harmonic relationship.

Osc Fine Frequency (Fine) — The relationship between oscillator frequency and note pitch is defined
by the Coarse and Fine parameters. Fine sets the ratio in fractions of whole numbers, creating an
inharmonic relationship.

Osc Fixed Frequency On (Fixed) — In Fixed Mode, oscillators do not respond to note pitch but
instead play a fixed frequency.

Osc Fixed Frequency (Freq) — This is the frequency of the oscillator in Hertz. This frequency is
constant, regardless of note pitch.

Osc Fixed Multiplier (Multi) — This is used to adjust the range of the fixed frequency. Multiply this
value with the value of the oscillator’s Freq knob to get actual frequency in Hz.

Osc Output Level (Level) — This sets the output level of the oscillator. If this oscillator is modulating
another, its level has significant influence on the resulting timbre. Higher levels usually create bright
and/or noisy sounds.

Envelope / Oscillator Switches — These switches toggle the display between the oscillator’s envelope
and its harmonics editor.

16/32/64 — These switches set the number of partials that are available for user editing.

Osc Waveform (Wave) — Choose from a collection of carefully selected waveforms. You can then
edit them via the harmonics editor.

Osc Feedback (Feedback) — An oscillator can modulate itself if it is not modulated by another
oscillator. The modulation is dependent not only on the setting of the feedback control but also on the
oscillator level and the envelope. Higher feedback creates a more complex resulting waveform.

Osc Phase (Phase) — This sets the initial phase of the oscillator. The range represents one whole cycle.

Retrigger (R) — When enabled, the oscillator restarts at the same position in its phase each time a note
is triggered. With R disabled, the oscillator is free-running.

Repeat — Higher harmonics can be generated by repeating the drawn partials with a gradual
fadeout, based on the settings in the Repeat chooser. Low Repeat values result in a brighter sound,
while higher values result in more high-end roll-off and a more prominent fundamental. With Repeat
off, partials above the 16th, 32nd or 64th harmonic are truncated.

Osc Frequency < Velocity (Osc < Vel) — The frequency of an oscillator can be modulated by note
velocity. Positive values raise the oscillator’s pitch with greater velocities, and negative values lower it.

Osc Freq < Vel Quantized (Q) — This allows quantizing the effect of the Frequency < Velocity
parameter. If activated, the sonic result is the same as manually changing the Coarse parameter for
each note.

Volume Envelope Rates < Velocity (Time < Vel) — This parameter exists for filter, pitch, LFO and
volume envelopes. It is therefore listed in the section on envelopes.

Osc Output Level < Velocity (Vel) — This defines how much the oscillator’s level depends upon note
velocity. Applying this to modulating oscillators creates velocity-dependent timbres.

Osc Output Level < Key (Key) — This defines how much the oscillator’s level depends upon note pitch.
The center point for this function is C3.

28.9.10.7 Envelope Display

Envelope Attack Time (Attack) — This sets the time it takes for a note to reach the peak level, starting
from the initial level. For the oscillator envelopes, the shape of this segment of the envelope is linear.
For the filter and pitch envelopes, the shape of the segment can be adjusted.

Envelope Decay Time (Decay) — This sets the time it takes for a note to reach the sustain level from the
peak level. For the oscillator envelopes, the shape of this segment of the envelope is exponential. For
the filter and pitch envelopes, the shape of the segment can be adjusted.

Envelope Release Time (Release) — This is the time it takes for a note to reach the end level after a
Note Off message is received. For the oscillator envelopes, this level is always -inf dB and the shape
of the segment is exponential. For the filter and pitch envelopes, the end level is determined by the
End Level parameter and the shape of the segment can be adjusted. This envelope segment will begin
at the value of the envelope at the moment the Note Off message occurs, regardless of which
segment is currently active.

Envelope Initial Level (Initial) — This sets the initial value of the envelope.

Envelope Peak Level (Peak) — This is the peak level at the end of the note attack.

Envelope Sustain Level (Sustain) — This is the sustain level at the end of the note decay. The envelope
will stay at this level until note release unless it is in Loop, Sync or Beat Mode.

Envelope End Level (End) — (LFO, Filter and pitch envelopes only) This is the level reached at the end
of the Release stage.

Envelope Loop Mode (Loop) — If this is set to Loop, the envelope will start again after the end of the
decay segment. If set to Beat or Sync, it will start again after a given beat-time. In Sync Mode, this
behavior will be quantized to song time. In Trigger mode, the envelope ignores Note Off.

Envelope Beat/Sync Rate (Repeat) — The envelope will be retriggered after this amount of beat-time,
as long as it is still on. When retriggered, the envelope will move at the given attack rate from the
current level to the peak level.

Envelope Loop Time (Time) — If a note is still on after the end of the decay/sustain segment, the
envelope will start again from its initial value. The time it takes to move from the sustain level to the
initial value is defined by this parameter.

Envelope Rates < Velocity (Time < Vel) — Envelope segments will be modulated by note velocity as
defined by this setting. This is especially interesting if the envelopes are looping. Note that this
modulation does not influence the beat-time in Beat or Sync Modes, but the envelope segments
themselves.

The filter and pitch envelopes also provide parameters that adjust the slope of their envelope
segments. Positive slope values cause the envelope to move quickly at the beginning, then slower.
Negative slope values cause the envelope to remain flat for longer, then move faster at the end. A
slope of zero is linear; the envelope will move at the same rate throughout the segment.

Attack Slope (A.Slope) — Adjusts the shape of the Attack envelope segment.

Decay Slope (D.Slope) — Adjusts the shape of the Decay envelope segment.

Release Slope (R.Slope) — Adjusts the shape of the Release envelope segment.

28.9.10.8 Context Menu Options for Operator

Certain operations and parameters in Operator are only available via the context menu. These
include:

Copy commands for Oscillators — The context menu of the oscillator’s shell and envelope display
provide options for copying parameters between oscillators.

Envelope commands — The context menu for all envelope displays provide options to quickly set all
envelope levels to maximum, minimum, or middle values.

Harmonics editor commands — The context menu for the harmonics editor can restrict partial drawing
to even or odd harmonics and toggle normalization of an oscillator’s output level. There is also a
command to export the waveform as an .ams file.

Play By Key — This command, in the context menu for the filter’s Freq control, optimizes the filter for
key tracking by setting the cutoff to 466 Hz and setting the Freq < Key to 100%.

Enable Per-Note Pitch Bend — This option is enabled by default so that Operator responds to per-
note pitch bend changes. If needed, you can deactivate this behavior by deselecting the option in the
device title bar’s context menu.

28.10 Sampler

The Sampler Instrument.

Sampler is a sleek yet formidable multisampling instrument that takes full advantage of Live‘s agile
audio engine. It has been designed from the start to handle multi-gigabyte instrument libraries with
ease, and it imports most common library formats. But with Sampler, playback is only the beginning;
its extensive internal modulation system, which addresses nearly every aspect of its sound, makes it
the natural extension of Live‘s sound-shaping techniques.

28.10.1 Getting Started with Sampler

Getting started with Sampler is as easy as choosing a preset from the browser. Like all of Live‘s
devices, Sampler’s presets are located in folders listed beneath its name. Presets imported from third-
party sample libraries are listed here, too, in the Imports folder.

Once you have loaded a Sampler preset into a track, remember to arm the track for recording (which
also enables you to hear any MIDI notes you might want to play), and then start playing!

28.10.2 Multisampling

Before going on, let’s introduce the concept of multisampling. This technique is used to accurately
capture the complexity of instruments that produce dynamic timbral changes. Rather than rely on the
simple transposition of a single recorded sample, multisampling captures an instrument at multiple
points within its critical sonic range. This typically means capturing the instrument at different pitches as
well as different levels of emphasis (played softly, moderately, loudly, etc.). The resulting multisample
is a collection of all the individually recorded sample files.

The acoustic piano, for example, is a commonly multisampled instrument. Because the piano’s pitch
and dynamic ranges are very wide and timbrally complex, transposing one sample across many
octaves would not reproduce the nuances of the instrument. Since multisampling relies on different
sound sources, three or more samples per piano key could be made (soft, medium, loud, very loud,
and so on), maximizing the sampler’s expressive possibilities.

Sampler is designed to let you approach multisampling on whatever level you like: you can load and
play multisample presets, import multisamples from third-party vendors, or create your own

multisamples from scratch. Lastly, you do not have use multisamples at all — drop a single sample into
Sampler and take advantage of its internal modulation system however you like.

28.10.3 Title Bar Options

Sampler’s Title Bar Context Menu.

Before delving into Sampler’s deep modulation features, let’s look at Sampler’s title bar context menu
options.

Although Cut, Copy, Rename, Edit Info Text, and Delete should already be familiar, the other entries
deserve some explanation:

Group — Selecting this will load Sampler into a new Instrument Rack.

Fold — Folds Sampler so that only the device title bar is visible. Unfold quickly by double-clicking the
device title bar.

Show Preset Name — By default, Sampler takes the top-most sample in the sample layer list as its title.
Unchecking Show Preset Name will replace the current title with “Sampler.”

Lock to Control Surface — Locks Sampler to a natively supported control surface defined in the Link,
Tempo & MIDI Settings, guaranteeing hands-on access no matter where the current focus is in your
Live Set. By default, Sampler will automatically be locked to the control surface when the track is
armed for recording. A hand icon in the title bar of locked devices serves as a reminder of their
statuses.

Save as Default Preset — Saves the current state of Sampler as the default preset.

Use Constant Power Fade for Loops — By default, Sampler uses constant-power fades at loop
boundaries. Uncheck this to enable linear crossfades at looping points.

Sampler -> Simpler — Converts Sampler presets to Simpler presets. This lets you easily share Sets with
other musicians even if they don’t use a Live edition that includes Sampler.

28.10.4 Sampler’s Tabs

Sampler’s Tabs in the Title Bar.

Sampler’s features are organized categorically into tabs (Zone, Sample, Pitch/Osc, Filter/Global,
Modulation and MIDI), accessed from Sampler‘s title bar. Clicking a tab will, with the exception of the
Zone tab, reveal its properties below. In addition to serving as an organizational aid, each tab has
one or more LEDs that indicate if there is modulation information in the corresponding area. We will
get to know Sampler by examining each of these tabs.

28.10.5 The Zone Tab

The Zone Tab.

Clicking on the Zone tab toggles the display of Sampler‘s Zone Editor, which offers a hands-on
interface for mapping any number of samples across three types of ranges — the Key Zone, the
Velocity Zone and Sample Select Editors, respectively.

The Key Zone Editor.

The Zone Editor opens in its own dedicated view, directly above the Device View. When used in
conjunction with Sampler’s other tabs, this layout greatly accelerates the creation and editing of
multisamples.

On the left side of the Zone Editor is the sample layer list, where multisamples are organized. All of the
individual samples belonging to a multisample are shown in this list, where they are referred to as
layers. For complex multisamples, this list can be quite long.

Above the sample layer list are various buttons for configuring the sample layers and toggling the
different editors:

Auto Select (Auto) — As MIDI notes arrive at Sampler, they are filtered by each sample layer’s key,
velocity and sample select zones. With Auto Select enabled, all sample layers that are able to play
an incoming note will become selected in the sample layer list for the duration of that note.

Zone Fade Mode (Lin/Pow) — This button toggles the fade mode of all zones between linear and
constant-power (exponential) slopes.

Round Robin (RR) — This button toggles Round Robin sample playback on or off.

Zone Editor View (Key/Vel/Sel) — These buttons toggle the display of the Key Zone, Velocity Zone
and Sample Select Editors.

The rest of the view is occupied by one of three editors that correspond to the sample layers: the Key
Zone Editor, the Velocity Zone Editor and the Sample Select Editor. These editors can be horizontally
zoomed by right-clicking within them to bring up a context menu, and selecting Small, Medium or
Large.

28.10.5.1 Round Robin Sample Playback

Using Different Samples for Round Robin Playback.

Round Robin is a playback method that triggers a different sample each time a note is played. This lets
you cycle through a set of samples in a defined order over time.

You can, for example, use Round Robin to cycle through samples of the same sound or note with
different articulations to add subtle nuances to repetitive drum or note patterns. You can also use it
with radically different-sounding samples to create unexpected rhythmic or tonal changes throughout
a pattern.

To use Round Robin, enable the RR toggle in the Zone Editor.

Enable the RR Toggle to Activate Round Robin Playback.

Once enabled, any samples in the sample layer list that share the same key zone can be triggered
when a note within that range is played.

You can select an option in the Round Robin Mode chooser to determine how the samples are
triggered:

Forward — Cycles through samples in order starting from the top of the sample layer list to the bottom.
Once the last sample is played, the cycle begins again from the topmost sample.

Backward — Cycles through samples in order starting from the bottom of the sample layer list to the
top. The cycle is repeated once the topmost sample is played.

Other — Cycles through samples randomly; the same sample will never be triggered twice in a row.

Random — Cycles through samples randomly; multiple retriggers of the same sample are possible.

The Round Robin Mode Chooser.

You can set a specific interval at which the cycle restarts via the Reset Interval chooser. This is useful for
triggering samples predictably and consistently. For example, if the Round Robin Mode is set to
Forward with a reset interval of 1 bar, the topmost sample triggers on the first note of each bar. In
Backward mode, the cycle restarts from the bottommost sample. In Other or Random mode, the cycle
restarts from the sample that was first played.

The Reset Interval Chooser.

28.10.5.2 The Sample Layer List

The Sample Layer List.

All samples contained in the currently loaded multisample are listed here, with each sample given its
own layer. For very large multisamples, this list might be hundreds of layers long! Fortunately, layers
can be descriptively named (according to their root key, for example). Mousing over a layer in the list
or a zone in the zone editors will display relevant information about the corresponding sample in the
Status Bar (bottom of screen). Selecting any layer will load its sample into the Sample tab for
examination.

Right-clicking within the sample layer list opens a context menu that offers options for sorting and
displaying the layers, distributing them across the keyboard and various other sample management
and “housekeeping“ options.

Delete — Deletes the currently selected sample(s).

Duplicate — Duplicates the currently selected sample(s).

Rename — Renames the selected sample.

Distribute Ranges Equally — Distributes samples evenly across the editor’s full MIDI note range (C-2
to G8).

Distribute Ranges Around Root Key — For layers that have different root keys, this option will distribute
their ranges as evenly as possible around their root keys, but without overlapping. For layers that
share a root key, the ranges will be distributed evenly.

Small/Medium/Large — Adjusts the zoom level of the Zone Editor.

Show in Browser — Navigates to the selected sample in the browser and selects it.

Manage Sample — Opens the File Manager and selects the chosen sample.

Normalize Volume — Adjusts Sampler’s Volume control so that the highest peak of each selected
sample uses the maximum available headroom.

Normalize Pan — Adjusts Sampler’s Pan control so that each selected sample has equal volume
across the stereo spectrum. Note that this does not necessarily return panned stereo samples to the
center position; rather, Live intelligently calculates a pan position for an even stereo spread.

Select All With Same Range — Selects all layers whose zone range matches the currently selected
layer. The results will change depending on which Zone Editor (Key, Velocity or Sample Select) is
active.

Sort Alphabetically (Ascending and Descending) — Arranges samples alphabetically according to
their names.

Sort by Key (Ascending and Descending) — Sorts key zones in an ascending or descending pattern.

Sort by Velocity (Ascending and Descending) — Sorts velocity zones in an ascending or descending
pattern.

Sort by Selector (Ascending and Descending) — Sorts sample select zones in an ascending or
descending pattern.

28.10.5.3 Key Zones

The Key Zone Editor.

Key zones define the range of MIDI notes over which each sample will play. Samples are only
triggered when incoming MIDI notes lie within their key zone. Every sample has its own key zone,
which can span anywhere from a single key up to the full 127.

A typical multisampled instrument contains many individual samples, distributed into many key zones.
Samples are captured at a particular key of an instrument’s voice range (known as their root key), but
may continue to sound accurate when transposed a few semitones up or down. This range usually
corresponds to the sample’s key zone; ranges beyond this zone are represented by additional
samples, as needed.

By default, the key zones of newly imported samples cover the full MIDI note range. Zones can be
moved and resized like clips in the Arrangement View, by dragging their right or left edges to resize
them, then dragging them into position.

Zones can also be faded over a number of semitones at either end by dragging their top right or left
corners. This makes it easy to smoothly crossfade between adjacent samples as the length of the
keyboard is traversed. The Lin and Pow boxes above the sample layer list indicate whether the zones
will fade in a linear or exponential manner.

28.10.5.4 Velocity Zones

The Velocity Zone Editor.

Velocity zones determine the range of MIDI Note On velocities (1-127) that each sample will respond
to. The timbre of most musical instruments changes greatly with playing intensity. Therefore, the best
multisamples capture not only individual notes, but also each of those notes at different velocities.

The Velocity Zone Editor, when toggled, appears alongside the sample layer list. Velocity is measured
on a scale of 1-127, and this number range appears across the top of the editor. The functionality of
the Velocity Zone Editor is otherwise identical to that of the Key Zone Editor.

28.10.5.5 Sample Select Zones

The Sample Select Editor.

Each sample also has a Sample Select zone, which is a data filter that is not tied to any particular
kind of MIDI input. Sample Select zones are very similar to the Chain Select Zones found in Racks, in
that only samples with sample select values that overlap the current value of the sample selector will
be triggered.

The Sample Select Editor, when toggled, appears alongside the sample layer list. The editor has a
scale of 0-127, similar to the Velocity Zone Editor. Above the value scale is the draggable indicator
known as the sample selector.

The Sample Selector.

The position of the sample selector only determines which samples are available for triggering. Once
a sample has been triggered, changing the position of the sample selector will not switch to a different
sample during playback.

28.10.6 The Sample Tab

The Sample Tab.

The playback behavior of individual samples is set within the Sample tab. Most of this tab is dedicated
to displaying the waveform of the currently selected sample. Hovering your mouse over the waveform
will display relevant information about the sample in the Status Bar (bottom of screen). It is important
to keep in mind that most of the values in this tab reflect the state of the currently selected sample only.
The Sample chooser always displays the current sample layer’s name, and is another way to switch
between layers when editing.

To zoom in the current sample, scroll with the mousewheel or trackpad while holding the Ctrl
(Win) / Cmd (Mac) modifier.

Reverse — This is a global, modulatable control that reverses playback of the entire multisample.
Unlike the Reverse function in the Clip View, a new sample file is not generated. Instead, sample
playback begins from the Sample End point, proceeds backwards through the Sustain Loop (if active),
and arrives at the Sample Start point.

Snap — Snaps all start and end points to the waveform zero-crossings (points where the amplitude is
zero) to avoid clicks. You can quickly see this by using Snap on square wave samples. As with
Simpler, this snap is based on the left channel of stereo samples, so a small Crossfade value may be
necessary in some cases to completely eliminate clicks. You can snap individual loop regions by right-
clicking on a loop brace and selecting “Snap Marker.”

Sample — Displays the name of the current sample layer, and can be used to quickly select different
layers of the loaded multisample.

Root Key (RootKey) — Defines the root key of the current sample.

Detune — Sample tuning can be adjusted here by +/- 50 cents.

Volume — A wide-range volume control, variable from full attenuation to a gain of +24 dB.

Pan — Samples can be individually panned anywhere in the stereo panorama.

28.10.6.1 Sample Playback

All of the following parameters work in conjunction with the global volume envelope (in the Filter/
Global tab) to create the basic voicing of Sampler. These envelopes use standard ADSR (Attack,
Decay, Sustain, Release) parameters, among others:

Envelope Attack Time (Attack) — This sets the time it takes for an envelope to reach the peak level,
starting from the initial level. The shape of the attack can be adjusted via the Attack Slope (A. Slope)
parameter.

Envelope Decay Time (Decay) — This sets the time it takes for an envelope to reach the sustain level
from the peak level. The shape of the decay can be adjusted via the Decay Slope (D. Slope)
parameter.

Envelope Sustain Level (Sustain) — This is the sustain level at the end of the envelope decay. The
envelope will stay at this level until note release unless it is in Loop, Sync or Beat Mode.

Envelope Release Time (Release) — This is the time it takes for an envelope to reach the end level after
a Note Off message is received. The shape of this stage of the envelope is determined by the Release
Slope (R. Slope) value.

Envelope Initial Level (Initial) — This sets the initial value of the envelope.

Envelope Peak Level (Peak) — This is the peak level at the end of the envelope attack, and the
beginning of the Decay stage.

Envelope End Level (End) — (LFO, Filter and pitch envelopes only) This is the level reached at the end
of the Release stage.

Envelope Rates < Velocity (Time < Vel) — Envelope segments will be modulated by note velocity as
defined by this setting. This is especially interesting if the envelopes are looping. Note that this
modulation does not influence the beat-time in Beat or Sync Modes, but the envelope segments
themselves.

Envelope Loop Mode (Loop) — If this is set to Loop, the envelope will start again after the end of the
decay segment. If set to Beat or Sync, it will start again after a given beat-time. In Sync Mode, this
behavior will be quantized to song time. In Trigger mode, the envelope ignores Note Off.

Envelope Beat/Sync Rate (Repeat) — The envelope will be retriggered after this amount of beat-time,
as long as it is still on. When retriggered, the envelope will move at the given attack rate from the
current level to the peak level.

Envelope Loop Time (Time) — If a note is still on after the end of the decay/sustain segment, the
envelope will start again from its initial value. The time it takes to move from the sustain level to the
initial value is defined by this parameter.

As mentioned above, Sampler’s envelopes also provide parameters that adjust the slope of their
envelope segments. Positive slope values cause the envelope to move quickly at the beginning, then
slower. Negative slope values cause the envelope to remain flat for longer, then move faster at the
end. A slope of zero is linear; the envelope will move at the same rate throughout the segment.

All time-based values in this tab are displayed in either samples or minutes:seconds:milliseconds,
which can be toggled using the context menu on any of their parameter boxes. Samples, in this
context, refer to the smallest measurable unit in digital audio, and not to the audio files themselves,
which we more commonly refer to as “samples.“

Sample Start — The time value where playback will begin. If the volume envelope’s Attack parameter
is set to a high value (slow attack), the audible result may begin some time later than the value shown
here.

Sample End — The time value where playback will end (unless a loop is enabled), even if the volume
envelope has not ended.

Sustain Mode — The optional Sustain Loop defines a region of the sample where playback will be
repeated while the note is in the sustain stage of its envelope. Activating the Sustain Loop also allows
the Release Loop to be enabled. This creates several playback options:

No Sustain Loop — Playback proceeds linearly until either the Sample End is reached or the

volume envelope completes its release stage.

Sustain Loop Enabled — Playback proceeds linearly until Loop End is reached, when it jumps
immediately to Loop Start and continues looping. If Release Mode is OFF, looping will continue inside
the Sustain Loop until the volume envelope has completed its release stage.

Back-and-Forth Sustain Loop Enabled — Playback proceeds to Loop End, then reverses until it

reaches Loop Start, then proceeds again towards Loop End. If Release Mode is OFF, this pattern
continues until the volume envelope has completed its release stage.

Link — Enabling the Link switch sets Sample Start equal to Loop Start. Note that the Sample Start
parameter box doesn’t lose its original value — it simply becomes disabled so that it can be recalled
with a single click.

Loop Start — The Sustain Loop’s start point, measured in samples.

Loop End — The Sustain Loop’s end point, measured in samples.

Release Mode — Whenever the Sustain Loop is active, Release Mode can also be enabled.

 — The volume envelope’s release stage is active, but will occur within the Sustain Loop, with

playback never proceeding beyond Loop End.

Release Enabled — When the volume envelope reaches its release stage, playback will proceed

linearly towards Sample End.

Release Loop Enabled — When the volume envelope reaches its release stage, playback will

proceed linearly until reaching Sample End, where it jumps immediately to Release Loop and
continues looping until the volume envelope has completed its release stage.

Back-and-Forth Release Loop Enabled — When the volume envelope reaches its release stage,
playback will proceed linearly until reaching Sample End, then reverses until it reaches Release Loop,
then proceeds again towards Sample End. This pattern continues until the volume envelope has
completed its release stage.

Release Loop — sets the start position of the Release Loop. The end of the Release Loop is the Sample
End.

Sustain- and Release-Loop Crossfade (Crossfade) — Loop crossfades help remove clicks from loop
transitions. By default, Sampler uses constant-power fades at loop boundaries. But by turning off “Use
Constant Power Fade for Loops“ in the context menu, you can enable linear crossfades.

Sustain- and Release-Loop Detune (Detune) — Since loops are nothing more than oscillations, the
pitch of samples may shift within a loop, relative to the loop’s duration. Tip: this is especially
noticeable with very short loops. With Detune, the pitch of these regions can be matched to the rest of
the sample.

Interpolation (Interpol) — This is a global setting that determines the accuracy of transposed samples.
Be aware that raising the quality level above “Normal“ to “Good” or “Best” will place significant
demands on your CPU.

RAM Mode (RAM) — This is also a global control that loads the entire multisample into RAM. This
mode can give better performance when modulating start and end points, but loading large
multisamples into RAM will quickly leave your computer short of RAM for other tasks. In any case, it is
always recommended to have as much RAM in your computer as possible, as this can provide
significant performance gains.

Hovering the mouse over the waveform and right-clicking to access the context menu provides a
number of editing and viewing options. As with the context menu in the Sample Layer List, Show in
Browser, Manage Samples, Normalize Volumes and Normalize Pan are available. Additionally, you
can zoom in or out of playing or looping regions, depending on which Sustain and Loop Modes are
selected.

Finally, a few options remain on the far-right side of the Sample tab:

Vertical Zoom (slider) — Magnifies the waveform height in the sample display. This is for visual clarity
only, and does not affect the audio in any way.

B, M, L and R Buttons — These buttons stand for Both, Mono, Left and Right, and allow you to choose
which channels of the sample should be displayed.

28.10.7 The Pitch/Osc Tab

The Pitch/Osc Tab.

28.10.7.1 The Modulation Oscillator (Osc)

Sampler features one dedicated modulation oscillator per voice, which can perform frequency or
amplitude modulation (FM or AM) on the multisample. The oscillator is fully featured, with 21
waveforms (available in the Type chooser), plus its own loopable amplitude envelope for dynamic
waveshaping. Note that this oscillator performs modulation only — its output is never heard directly.
What you hear is the effect of its output upon the multisample.

FM — In this mode, the modulation oscillator will modulate the frequency of samples, resulting in more
complex and different-sounding waveforms.

AM — In this mode, the modulation oscillator will modulate the amplitude of samples. Subsonic
modulator frequencies result in slow or rapid variation in the volume level; audible modulator
frequencies result in composite waveforms.

The modulation oscillator is controlled via Initial, Peak, Sustain, End, Loop, Attack and Time <
Velocities parameters. For detailed information on how these work, see the Sample Playback section.
Additionally, the right side of the modulation oscillator section features the following controls:

Type — Choose the modulation oscillator’s waveform here.

Volume — This determines the intensity of the modulation oscillator’s sample modulation.

Vol < Vel — The modulation oscillator’s Volume parameter can be modified by the velocity of
incoming MIDI notes. This determines the depth of the modulation.

Fixed — When enabled, the modulation oscillator’s frequency will remain fixed at the rate determined
by the Freq and Multi parameters, and will not change in response to incoming MIDI notes.

Freq — With Fixed set to On, this rate is multiplied by the Multi parameter to determine the modulation
oscillator’s fixed frequency.

Multi — With Fixed set to On, the Freq parameter is multiplied by this amount to determine the
modulation oscillator’s fixed frequency.

Coarse — Coarse tuning of the modulation oscillator’s frequency (0.125-48). This is only available
when Fixed is set to Off.

Fine — Fine tuning of the modulation oscillator’s frequency (0-1000). This is only available when
Fixed is set to Off.

28.10.7.2 The Pitch Envelope

The pitch envelope modulates the pitch of the sample over time, as well as of the Modulation
Oscillator, if it is enabled. This is a multi-stage envelope with ADSR, Initial, Peak, and End levels, as
described in the Sample Playback section. The values of the envelope parameters can be adjusted via
the sliders, or by dragging the breakpoints in the envelope’s display.

On the lower-left of the Pitch Envelope section is the Amount slider. This defines the limits of the pitch
envelope’s influence, in semitones. The actual range depends upon the dynamics of the envelope
itself.

The right-hand side of this section contains five sliders and one chooser that are unrelated to the Pitch
Envelope, but can globally effect Sampler’s output:

Spread — When Spread is used, two detuned voices are generated per note. This also doubles the
processing requirements.

Transpose (Transp) — Global transpose amount, indicated in semitones.

Detune — Global detune amount, indicated in cents.

Key Zone Shift (Zn Shft) — This transposes MIDI notes in the Key Zone Editor only, so that different
samples may be selected for playback, even though they will adhere to the played pitch. Good for
getting interesting artifacts from multisamples.

Glide — The global Glide mode, used in conjunction with the Time parameter to smoothly transition
between pitches. ’Glide’ is a standard monophonic glide, while ’Portamento’ works polyphonically.

Time — Enabling a Glide mode produces a smooth transition between the pitch of played notes. This
parameter determines the length of the transition.

28.10.8 The Filter/Global Tab

The Filter/Global Tab.

28.10.8.1 The Filter

Sampler features a polyphonic filter with an optional integrated waveshaper. The filter section offers a
variety of filter types including low-pass, high-pass, band-pass, notch, and a special Morph filter.
Each filter can be switched between 12 and 24 dB slopes as well as a selection of analog-modeled
circuit behaviors developed in conjunction with Cytomic that emulate hardware filters found on some
classic analog synthesizers.

The Clean circuit option is a high-quality, CPU-efficient design that is the same as the filters used in EQ
Eight. This is available for all of the filter types.

The OSR circuit option is a state-variable type with resonance limited by a unique hard-clipping
diode. This is modeled on the filters used in a somewhat rare British monosynth, and is available for all
filter types.

The MS2 circuit option uses a Sallen-Key design and soft clipping to limit resonance. It is modeled on
the filters used in a famous semi-modular Japanese monosynth and is available for the low-pass and
high-pass filters.

The SMP circuit is a custom design not based on any particular hardware. It shares characteristics of
both the MS2 and PRD circuits and is available for the low-pass and high-pass filters.

The PRD circuit uses a ladder design and has no explicit resonance limiting. It is modeled on the filters
used in a legacy dual-oscillator monosynth from the United States and is available for the low-pass
and high-pass filters.

The most important filter parameters are the typical synth controls Frequency and Resonance.
Frequency determines where in the harmonic spectrum the filter is applied; Resonance boosts
frequencies near that point.

When using the low-pass, high-pass, or band-pass filter with any circuit type besides Clean, there is
an additional Drive control that can be used to add gain or distortion to the signal before it enters the
filter.

The Morph filter has an additional Morph control which sweeps the filter type continuously from low-
pass to band-pass to high-pass to notch and back to low-pass.

You can quickly snap the Morph control to a low-pass, band-pass, high-pass, or notch setting via
dedicated options in the context menu of the Morph slider.

To the right, the filter’s cutoff frequency can be modulated over time by a dedicated filter envelope.
This envelope works similarly to the envelopes in the Pitch/Osc tab, with Initial, Peak, Sustain and End
levels, ADSR, Loop mode and slope points. This area is toggled on/off with the F. Env button. The
Amount slider determines how much influence the filter envelope has on the filter’s cutoff frequency,
and needs to be set to a non-zero value for the envelope to have any effect.

Below the Filter is a waveshaper, which is toggled by clicking the Shaper button. Four different curves
can be chosen for the waveshaper in the Type selector: Soft, Hard, Sine and 4bit. Shaper’s overall
intensity can be controlled with the Amount slider. In addition, the signal flow direction can be
adjusted with the button above the waveshaper area: with the triangle pointing up, the signal passes
from the shaper to the filter; with the triangle pointing down, it passes from the filter to the shaper.

28.10.8.2 The Volume Envelope and Global Controls

The volume envelope is global, and defines the articulation of Sampler’s sounds with standard ADSR
(attack, decay, sustain, release) parameters. Please see the Sample Playback section for details on
these parameters.

This envelope can also be looped via the Loop chooser. When a Loop mode is selected, the Time/
Repeat slider becomes important. For Loop and Trigger modes, if a note is still held when the Decay
stage ends, the envelope will restart from its initial value. The time it takes to move from the Sustain
level to the initial value is defined by the Time parameter. For Beat and Sync modes, if a note is still
held after the amount set in the Repeat slider, the envelope will restart from its initial value.

The Pan slider is a global pan control (acting on all samples), while Pan < Rnd adds a degree of
randomness to the global pan position. Time (Global Time Envelope) will proportionally shrink or
expand the length of all envelopes in Sampler. Time < Key (Global Envelope Time < Key) will
proportionally shrink or expand the length of all envelopes in Sampler relative to the pitch of incoming
MIDI notes.

Finally, the Voices selector provides up to 32 simultaneous voices for each instance of Sampler. Voice
retriggering can optionally be enabled by activating the Retrigger button (R) to the right of the Voices
chooser. When activated, notes which are already playing will be retriggered, rather than generating
an additional voice. Turning Retrigger on can save CPU power, especially if a note with a long
release time is being triggered very often and very quickly.

28.10.9 The Modulation Tab

The Modulation Tab.

The Modulation tab offers an additional loopable envelope, plus three LFOs, all capable of
modulating multiple parameters, including themselves. Each LFO can be free running, or synced to the
Live Set’s tempo, and LFOs 2 and 3 can produce stereo modulation effects.

28.10.9.1 The Auxiliary Envelope

On the left, the Auxiliary (Aux) envelope functions much like the envelopes in the Pitch/Osc tab, with
Initial, Peak, Sustain and End levels, ADSR, Loop mode and slope points. This envelope can be routed
to 29 destinations in both the A and B choosers. How much the Auxiliary envelope will modulate
destinations A and B is set in the two sliders to the right.

28.10.9.2 LFOs 1, 2 and 3

The remaining space of the Modulation tab contains three Low Frequency Oscillators (LFOs). As the
name implies, Sampler’s LFOs operate by applying a low-frequency (below 30 Hz) to a parameter in
order to modulate it. Engage any of these oscillators by clicking the LFO 1, LFO 2 or LFO 3 switches.

Type — Sampler’s LFOs have 6 different waveshapes available: Sine, Square, Triangle, Sawtooth
Down, Sawtooth Up, and Sample and Hold.

Rate — With Hz selected, the speed of the LFO is determined by the Freq slider to the right. With the
note head selected, the LFO will be synced to beat-time, adjustable in the Beats slider to the right.

Freq — The LFO’s rate in Hertz (cycles per second), adjustable from 0.01 to 30 Hz.

Beats — This sets the LFO’s rate in beat-time (64th notes to 8 bars).

LFO Attack (Attack) — This is the time needed for the LFO to reach maximum intensity. Use this, for
example, to gradually introduce vibrato as a note is held.

LFO Retrigger (Retrig) — Enabling Retrigger for an LFO will cause it to reset to its starting point, or
initial phase, on each new MIDI note. This can create hybrid LFO shapes if the LFO is retriggered
before completing a cycle.

LFO Offset (Offset) — This changes the starting point, or initial phase of an LFO, so that it begins at a
different point in its cycle. This can create hybrid LFO shapes if the LFO is retriggered before
completing a cycle.

LFO Rate < Key (Key) — Also known as keyboard tracking, non-zero values cause an LFO’s rate to
increase relative to the pitch of incoming MIDI notes.

LFO 1 has four sliders for quickly modulating global parameters:

Volume (Vol) — LFO 1 can modulate the global volume level. This slider determines the depth of the
modulation on a 0-100 scale.

Pan (Pan) — LFO 1 can modulate the global pan position. This slider determines the depth of the
modulation on a 0-100 scale.

Filter — LFO 1 can modulate the filters cutoff frequency (Freq in the Filter/Global tab). This slider
determines the depth of the modulation on a 0-24 scale.

Pitch — LFO 1 can modulate the pitch of samples. This slider determines the depth of the modulation
on a 0-100 scale.

LFO Stereo Mode (Stereo) — LFOs 2 and 3 can produce two types of stereo modulation: Phase or
Spin. In phase mode, the right and left LFO channels run at equal speed, and the Phase parameter is
used to offset the right channel from the left. In spin mode, the Spin parameter can make the right LFO
channel run up to 50% faster than the left.

Like the Auxiliary envelope, LFOs 2 and 3 contain A and B choosers, where you can route LFOs to
many destinations.

28.10.10 The MIDI Tab

The MIDI Tab.

The MIDI tab’s parameters turn Sampler into a dynamic performance instrument. The MIDI controllers
Key, Velocity, Release Velocity, Aftertouch, Modulation Wheel, Foot Controller and Pitch Bend can be
mapped to two destinations each, with varying degrees of influence determined in the Amount A and
Amount B sliders.

For example, if we set Velocity’s Destination A to Loop Length, and its Amount A to 100, high
velocities will result in long loop lengths, while low velocities will create shorter ones.

At the bottom is a Pitch Bend Range slider (0 to 24 steps). The 14-bit range of pitch wheel values can
be scaled to produce up to 24 semitones of pitch bend in Sampler.

Finally, clicking in the Sampler image on the right will trigger a scrolling, movie-like credits for
Sampler. These are the people you can thank!

28.10.11 Importing Third-Party Multisamples

Sampler can use the following third-party sample formats:

•
•
•

REX files (supported in Live Standard and Suite only)
ACID Loops
Soundtrack Loops

Note that the tags in ACID Loops or Soundtrack Loops are not accessible in Live.

To import a third-party multisample, navigate to the file in Live‘s browser and drag it into a Live Set.
This will import it into your User Library.

Importing will create new Sampler presets, which you can find in the browser under User Library/
Sampler/Imports.

Note that some multisample files will be converted to Instrument Rack presets that contain several
Sampler instances used to emulate the original more accurately.

28.11 Simpler

The Simpler Instrument.

Simpler is an instrument that integrates the basic elements of a sampler with a set of classic synthesizer
parameters. A Simpler voice plays a user-defined region of a sample, which is in turn processed by
envelope, filter, LFO, volume and pitch components. But unlike a conventional sampler, Simpler
includes some unique functionality inherited from Live’s clips. Specifically, Simpler can play back
samples using Live’s warping. Warped samples will play back at the tempo of your Set, regardless of
which note you play. Warping in Simpler works in much the same way as it does in audio clips, and
bringing a warped clip into Simpler from an audio track, the browser, or your desktop preserves your

manual warp settings. For more information about warping, see the Audio Clips, Tempo, and Warping
chapter.

Simpler’s interface is divided into two sections: the Sample and Controls tabs. To get an even better
view, you can toggle the location of the Sample controls between the device chain and Live’s main
window by clicking the
parameters in the Controls tab fill Simpler in the Device View.

 button in Simpler’s title bar. When using this expanded view, the

The Sample Tab displays the sample waveform. Samples can be dragged into Simpler either directly
from the browser, or from the Session or Arrangement View in the form of clips. In the latter case,
Simpler will use only the section of the sample demarcated by the clip’s start/end or loop markers.
Any adjustments that have been made to a clip’s Warp Markers and other warping properties will be
retained when dragging a clip into Simpler. Samples can be replaced by dragging in a new sample,
or by activating the Hot-Swap button in the lower-right corner of the waveform display.

Hot-Swapping a Sample.

To zoom in the sample waveform, scroll with the mousewheel or trackpad while holding the Ctrl
(Win) / Cmd (Mac) modifier.

28.11.1 Playback Modes

The most important parameter that determines how Simpler will treat samples is the mode switch,
which is used to choose one of Simpler’s three playback modes. This switch is found on the left side of
the Sample tab or along the bottom of the expanded sample view.

Mode Switch in the Sample Tab.

Mode Switch in the Expanded View.

•

•

•

Classic Playback Mode is the default mode when using Simpler, and is optimized for creating
“conventional” melodic and harmonic instruments using pitched samples. It features a complete
ADSR envelope and supports looping, allowing for samples to sustain as long as a note is held
down. Classic Mode is polyphonic by default.
One-Shot Playback Mode is exclusively for monophonic playback, and is optimized for use
with one-shot drum hits or short sampled phrases. This mode has simplified envelope controls
and does not support looping. By default, the entire sample will play back when a note is
triggered, regardless of how long the note is held.
Slicing Playback Mode non-destructively slices the sample so that the individual slices can be
played back chromatically. You can create and move slices manually, or choose from a number
of different options for how Simpler will automatically create slices. This mode is ideal for
working with rhythmic drum breaks.

28.11.1.1 Classic Playback Mode

The Sample Tab in Classic Playback Mode.

In Classic Playback Mode, the various sample position controls change which region of the sample
you play back. These controls include the Start and Length parameters as well as the two “flags” that

appear in the waveform display. The left flag sets the absolute position in the sample from which
playback can start, while the End control sets where playback can end. Start and Length are then
represented in percentages of the total sample length enabled by the flags. For example, a Length
value of 50% will play exactly half of the region between the flags. The Loop slider determines how
much of the available sample will loop. This parameter is only active if the Loop switch is enabled.

It’s possible to create sustaining loops that are so short they take on a glitchy or granular character, or
even take on a pitch as a result of looping at audio rates. While this might be exactly the effect you
want, it can cause very high CPU loads, particularly when working with the Complex or Complex Pro
Warp Modes.

Quite often, you’ll start with a longer region of a sample and end up using only a small part of it.
Simpler’s waveform display can be zoomed and panned just as in other parts of Live — drag
vertically or scroll with the mousewheel or trackpad while holding the Ctrl (Win) / Cmd (Mac)
modifier to zoom, and drag horizontally to pan different areas of the sample into view. Zooming
works the same in all three playback modes.

Pressing the Loop On/Off button determines whether or not the sample will loop when a note is held
down. It is possible for glitches or pops to occur between a looped sample’s start and end points due
to the discontinuity in waveform amplitude (i.e., the sample’s loudness). The Snap switch will help
mitigate these by forcing Simpler’s loop and region markers to snap to zero-crossing points in the
sample (points where the amplitude is zero). Snapping is based on the left channel of stereo samples.
It is therefore still possible, even with Snap activated, to encounter glitches with stereo samples.

The transition from loop end to loop start can be smoothed with the Fade control, which crossfades the
two points. This method is especially useful when working with long, textural samples.

The Gain slider allows you to boost or cut the level of the sample. Note that this is a separate gain
stage from Simpler’s Volume knob, which determines the final output level of the entire instrument
(after processing through Simpler’s filter). This parameter is available in all three playback modes.

The Voices parameter sets the maximum number of voices that Simpler can play simultaneously. If
more voices are needed than have been allocated by the Voices chooser, “voice stealing“ will take
place, in which the oldest voice(s) will be dropped in favor of those that are new. For example, if your
Voices parameter is set to 8, and ten voices are all vying to be played, the two oldest voices will be
dropped. (Simpler does try to make voice stealing as subtle as possible.)

With Retrig enabled, a note that is already sustaining will be cut off if the same note is played again. If
Retrig is disabled, multiple copies of the same note can overlap. Note that Retrig only has an audible
effect if the sample has a long release time and the number of Voices is set to more than one.

The various warp parameters are the same in all three playback modes and are discussed below.

28.11.1.2 One-Shot Playback Mode

The Sample Tab in One-Shot Playback Mode.

In One-Shot Playback Mode, the left and right flags set the available playback region, as they do in
Classic Mode, but there are no Loop or Length controls. There is also no Voices control; One-Shot
Mode is strictly monophonic.

With Trigger enabled, the sample will continue playing even after the note is released; the amount of
time you hold the pad has no effect when Trigger is on.

You can shape the volume of the sample using the Fade In and Fade Out controls. Fade In determines
how long it takes the sample to reach its maximum volume after a note is played, while Fade Out
begins a fade out the specified amount of time before the end of the sample region.

With Gate enabled, the sample will begin fading out as soon as you release the note. The Fade Out
time determines how long it will take to fade to silence after release.

Snap works similarly to its function in Classic Mode, but only affects the start and end flags (because
there are no loop options.)

28.11.1.3 Slicing Playback Mode

The Sample Tab in Slicing Playback Mode.

In Slicing Playback Mode (as in One-Shot Playback Mode), the left and right flags set the available
playback region.

The Slice By chooser determines the specific way in which slices will be created:

•

Transient - Slices are placed on the sample’s transients automatically. The Sensitivity slider
determines how sensitive Simpler is to transient levels within the sample, and thus how many

slices will be automatically created. Higher numbers result in more slices, up to a maximum of
64 slices.
Beat - Slices are placed at musical beat divisions. The Division chooser selects the beat division
at which Simpler will slice the sample region.
Region - Slices are placed at equal time divisions. The Regions chooser selects the number of
evenly-spaced slices that will be created.
Manual - Slices are created manually, by double-clicking within the sample region. When
Manual is selected, no slices are placed automatically.

•

•

•

The Playback chooser determines how many slices can be triggered simultaneously. Mono is
monophonic; only one slice can be played at a time. When set to Poly, multiple slices can be
triggered together. The Voices and Retrig controls are available with Poly enabled, and work as they
do in Classic Playback Mode. When set to Thru, playback is monophonic, but triggering one slice will
continue playback through the rest of the sample region.

The Trigger/Gate switch works the same as it does in One-Shot Playback Mode. The Fade In and Out
controls behave slightly differently, depending on the setting of the Playback chooser. With Mono or
Poly selected, the Fade times are measured from the beginning to the end of each individual slice,
while with Thru selected, they are measured from the triggered slice to the end of the region. This
means that the fade times may sound different depending on where in the region you trigger.

Automatically created slices appear as vertical blue lines on the waveform display. Double-clicking a
slice deletes it. If you’re not satisfied with Simpler’s automatic slice placement, you can click and drag
a slice to move it to a new position. Double-clicking on the waveform between slices will create
manual slices, which appear white. In Transients mode, holding Alt (Win) / Option (Mac) and
clicking on a slice will toggle it between a manual and automatic slice. Manually created slices in
Transients mode are preserved regardless of the Sensitivity amount.

28.11.2 Warp Controls

Simpler’s Warp Controls.

When the Warp switch is off, Simpler behaves like a “conventional” sampler; as you play back the
sample at different pitches, the sample plays back at different speeds. In some cases, this is exactly the
effect that you want. But when working with samples that have their own inherent rhythm, you may
want to enable Warp. This will cause Simpler to play back the sample in sync with your current song
tempo, regardless of which notes you play.

If you’re familiar with how warping works in audio clips, you’ll find that Simpler’s Warp Modes and
settings behave in the same way. For more information, see the section called Warp Modes.

The Warp as… button adjusts the warping of the sample so that it will play back precisely within the
specified number of bars or beats. Live makes its best guess about what this value should be based on
the length of the sample, but if it gets it wrong, you can use the ÷2 or ×2 buttons to double or halve the
playback speed, respectively.

28.11.3 Filter

Simpler’s Filter Controls.

Simpler’s filter section offers a variety of filter types including low-pass, high-pass, band-pass, notch,
and a special Morph filter. Each filter can be switched between 12 and 24 dB slopes as well as a
selection of analog-modeled circuit behaviors developed in conjunction with Cytomic that emulate
hardware filters found on some classic analog synthesizers.

The Clean circuit option is a high-quality, CPU-efficient design that is the same as the filters used in EQ
Eight. This is available for all of the filter types.

The OSR circuit option is a state-variable type with resonance limited by a unique hard-clipping
diode. This is modeled on the filters used in a somewhat rare British monosynth, and is available for all
filter types.

The MS2 circuit option uses a Sallen-Key design and soft clipping to limit resonance. It is modeled on
the filters used in a famous semi-modular Japanese monosynth and is available for the low-pass and
high-pass filters.

The SMP circuit is a custom design not based on any particular hardware. It shares characteristics of
both the MS2 and PRD circuits and is available for the low-pass and high-pass filters.

The PRD circuit uses a ladder design and has no explicit resonance limiting. It is modeled on the filters
used in a legacy dual-oscillator monosynth from the United States and is available for the low-pass
and high-pass filters.

The most important filter parameters are the typical synth controls Frequency and Resonance.
Frequency determines where in the harmonic spectrum the filter is applied; Resonance boosts
frequencies near that point.

When using the low-pass, high-pass, or band-pass filter with any circuit type besides Clean, there is
an additional Drive control that can be used to add gain or distortion to the signal before it enters the
filter.

The Morph filter has an additional Morph control which sweeps the filter type continuously from low-
pass to band-pass to high-pass to notch and back to low-pass.

You can quickly snap the Morph control to a low-pass, band-pass, high-pass, or notch setting via
dedicated options in the context menu of the Morph knob.

The Frequency and Envelope buttons in the filter section’s display area toggle between showing the
filter’s frequency response and its envelope. Filter cutoff frequency and resonance can be adjusted via
the knobs or by dragging the filter response curve in the display area. Filter frequency can also be
modulated by the following:

•
•
•
•

Note velocity, via the Vel control in the filter’s display.
Note pitch, via the Key control in the filter’s display.
Filter envelope, via the Envelope control in the filter’s display.
LFO, via the Filter slider in the LFO section.

28.11.4 Envelopes

Simpler’s Filter and Amplitude Envelope Controls.

Simpler contains three classic ADSR envelopes, as seen in most synthesizers, for shaping the dynamic
response of the sample. Amplitude, filter frequency, and pitch modulation are all modifiable by
toggling their respective buttons in the envelope section. Attack controls the time in milliseconds that it
takes for the envelope to reach its peak value after a note is played. Decay controls the amount of
time it takes for the envelope to drop down to the Sustain level, which is held until the note is released.
Release time is the amount of time after the end of the note that it takes for the envelope to drop from
the Sustain level back down to zero. These parameters can be adjusted via their dedicated controls or
graphically, by dragging the handles within the envelope visualizations.

The influence of envelopes on the filter cutoff and pitch can be set using the envelope amount controls
in the top right of each of these sections.

The Filter and Pitch Envelope Amount Controls.

The Amplitude Envelope can be looped via the Loop Mode chooser. For Loop and Trigger modes, if a
note is still held when the Decay stage ends, the envelope will restart from its initial value. The time it
takes to move from the Sustain level to the initial value is defined by the Time parameter. For Beat and
Sync modes, if a note is still held after the amount set in the Rate slider, the envelope will restart from
its initial value.

The Amplitude Envelope Loop Mode Chooser and Time Control.

28.11.5 LFO

Simpler’s LFO Section.

The LFO (low-frequency oscillator) section offers sine, square, triangle, sawtooth down, sawtooth up
and random waveforms. The LFO runs freely at frequencies between 0.01 and 30 Hz, or synced to
divisions of the Set’s tempo. LFOs are applied individually to each voice, or played note, in Simpler.

The time required for the LFO to reach full intensity is determined by the Attack control. The R switch
toggles Retrigger. When enabled, the LFO’s phase is reset to the Offset value for each new note. Note
that Offset has no effect when Retrigger is disabled.

The Key parameter scales each LFO’s Rate in proportion to the pitch of incoming notes. A high Key
setting assigns higher notes a higher LFO rate. If Key is set to zero, all voices’ LFOs have the same rate
and may just differ in their phase.

The Volume, Pitch, Pan, and Filter sliders determine how much the LFO will modulate the volume, pitch,
pan, and filter, respectively.

28.11.6 Global Parameters

Simpler’s Global Parameters.

Panorama is defined by the Pan control, but can be further swayed by randomness (via the Random >
Pan slider) or modulated by the LFO.

Simpler also offers a special Spread parameter that creates a rich stereo chorus by using two voices
per note and panning one to the left and one to the right. The two voices are detuned, and the amount
of detuning can be adjusted with the Spread control.

Whether or not spread is applied to a particular note depends upon the setting of the Spread
parameter during the Note On event. To achieve special effects, you could, for instance, create a
sequence where Spread is zero most of the time and turned on only for some notes. These notes will
then play in stereo, while the others will play mono.

The output volume of Simpler is controlled by the Volume control, which can also be dependent upon
note velocity, as adjusted by the Velocity > Volume control. Tremolo effects can be achieved by
allowing the LFO to modulate the Volume parameter.

Simpler plays back a sample at its original pitch if the incoming MIDI note is C3, however the
Transpose control allows transposing this by +/- 48 semitones. Pitch can also be modulated by the
LFO or pitch envelope. The pitch envelope is especially helpful in creating percussive sounds. Simpler
reacts to MIDI Pitch Bend messages with a sensitivity of +/- 5 semitones. You can also modulate the
Transpose parameter with clip envelopes and external controllers. For fine tuning of the pitch, use the
Detune control, which can be adjusted +/- 50 cents.

Simpler includes a glide function. When this function is activated, new notes will start from the pitch of
the last note played and then slide gradually to their own pitch. Two glide modes are available:
Glide, which works monophonically, and Portamento, which works polyphonically. The speed of the
glide is set with the Time control.

28.11.7 Context Menu Options for Simpler

A number of Simpler’s features are only accessible by opening the context menu via the sample
display or Simpler’s title bar.

By default, Simpler uses constant-power fades. But by turning off “Use Constant Power Fade for
Loops“ in the context menu of Simpler’s title bar, you can enable linear crossfades. Note that the Fade
parameter is not available when warp is enabled.

Presets created in Simpler can be converted for use in Sampler, and vice-versa. To do this, right-click
on Simpler’s title bar and choose the Simpler -> Sampler command. In this way, presets created in
Simpler can be in a multisample context in Sampler. Note, however, that Simpler’s warping and
slicing functionality is not available in Sampler, and presets that use any of these functions will sound
and behave very differently in Sampler.

Manage Sample reveals the loaded sample in Live’s File Manager, while the Show in Browser option
reveals the sample in Live’s browser. Show in Finder/Explorer reveals the sample within its folder in
your computer’s operating system. Note that this command is not available when working with
samples that have been loaded from official Ableton Packs.

Normalize Volumes adjusts the volume of the loaded sample so that its highest peak uses all of the
available headroom.

Crop removes the portions of the sample that are outside of the Start and End points, while Reverse
plays the entire sample backwards. Note that both Crop and Reverse are non-destructive; they create
a copy of the sample and apply the process to the copy, so your original sample is not changed.

When working in Slicing Playback Mode, two additional context menu options are available: Slice to
Drum Rack replaces the Simpler with a Drum Rack in which each of the current slices is split onto its
own pad. Slice to New MIDI Track is similar, but this creates an additional track containing a Drum
Rack rather than replacing the current Simpler. Additionally, when slicing to a new track, a clip is
created that plays back the slices in order. For more about slicing, see the dedicated section for this
topic.

28.11.8 Strategies for Saving CPU Power

Real-time synthesis needs lots of computing power. However, there are strategies for reducing CPU
load. Save the CPU spent on Simpler by doing some of the following:

•

•
•

•
•

When using warping, be aware that the Complex and Complex Pro modes use significantly
more CPU power than the other Warp Modes.
Turn off the Filter if it is not needed.
A filter’s CPU cost correlates with the steepness of its slope — the 24 dB slope is more
expensive than the 12 dB slope.
Turn off the LFO for a slightly positive influence on CPU.
Stereo samples need significantly more CPU than mono samples, as they require twice the
processing.

•
•

Decrease the number of simultaneously allowed voices with the Voices control.
Turn Spread to 0% if it is not needed.

28.12 Tension

The Tension Instrument.

Tension is a synthesizer dedicated to the emulation of string instruments, and developed in
collaboration with Applied Acoustics Systems. The synthesizer is entirely based on physical modeling
technology and uses no sampling or wavetables. Instead, it produces sound by solving mathematical
equations that model the different components in string instruments and how they interact. This
elaborate synthesis engine responds dynamically to the control signals it receives while you play
thereby reproducing the richness and responsiveness of real string instruments.

Tension features four types of exciters (two types of hammer, a pick and a bow), an accurate model
of a string, a model of the fret/finger interaction, a damper model and different types of
soundboards. The combination of these different elements allows for the reproduction of a wide range
of string instruments. Tension is also equipped with filters, LFOs, envelope parameters, and MPE
support, which extend the sound sculpting possibilities beyond what would be possible with “real-
world“ instruments. Finally, Tension offers a wide range of performance features, including keyboard
modes, portamento, vibrato, and legato functions.

28.12.1 Architecture and Interface

It is the vibration from the string which constitutes the main sound production mechanism of the
instrument. The string is set into motion by the action of an exciter which can be a hammer, a pick or a
bow. The frequency of the oscillation is determined by the effective length of the string, which is
controlled by the finger/fret interaction or termination. A damper can be applied to the strings in
order to reduce the decay time of the oscillation. This is the case on a piano, for example, when felt is
applied to the strings by releasing the keys and sustain pedal. The vibration from the string is then
transmitted to the body of the instrument, which can radiate sound efficiently. In some instruments, the
string vibration is transmitted directly to the body through the bridge. In other instruments, such as the
electric guitar, a pickup is used to transmit the string vibration to an amplifier. In addition to these main

sections, a filter section has been included between the string and body sections in order to expand
the sonic possibilities of the instrument.

The Tension interface is divided into two main tabs, which are further divided into sections. The String
tab contains all of the fundamental sound producing components related to the string itself: Exciter,
Damper, String, Vibrato, Termination, Pickup, and Body. The Filter/Global tab contains the Filter
section and the MPE section, as well as controls for global performance parameters. Each section
(with the exception of String and the global Keyboard section) can be enabled or disabled
independently. Turning off a section reduces CPU usage.

28.12.2 String Tab

The String tab contains the parameters related to the physical properties of the string itself, as well as
the way in which it’s played.

28.12.2.1 The Exciter Section

Tension’s Exciter Section.

28.12.2.2 Exciter Types

The modeled string can be played using different types of exciters in order to reproduce different
types of instruments and playing techniques.

The Exciter section can be toggled on or off via the switch next to its name. With it off, the string can
only be activated by interaction with its damper. If both the Exciter and Damper sections are
deactivated, nothing can set the string in motion — if you find that you’re not producing any sound,
check to see that at least one of these sections is on.

The Exciter Type chooser offers four choices - Bow, Hammer, Hammer (bouncing) and Plectrum.

Bow — this exciter is associated with bowed instruments such as the violin, viola or cello. The bow sets
the string in sustained oscillation. The motion of the bow hair across the string creates friction, causing
the string to alternate between sticking to the hair and breaking free. The frequency of this alternation
between sticking and slipping determines the fundamental pitch. Note that the Damping knob is
unavailable when the Bow exciter is selected.

Hammer — this exciter type simulates the behavior of soft hammers or mallets. Hammer models a
hammer that is located below the string and strikes it once before falling away. This type of
mechanism is found in a piano, for example.

Hammer (bouncing) - this exciter type is similar to Hammer, except that it models a hammer that is
located above the string and is dropped onto it, meaning that it can bounce on the string multiple
times. This playing mode can be found on a hammered dulcimer, for example.

Plectrum — a plectrum or “pick“ is associated with instruments such as guitars and harpsichords. It can
be thought of as an angled object placed under the string that snaps the string into motion.

28.12.2.3 Exciter Parameters

Next to the Exciter Type chooser are five parameter knobs. The first two parameters vary depending
on the chosen Exciter Type, whereas the last three parameters are universal.

Bow Parameters:

•

•

The Force knob adjusts the amount of pressure being applied to the string by the bow. The
sound becomes more “scratchy“ as you increase this value.
The Friction knob adjusts the amount of friction between the bow and the string. Higher values
usually result in a faster attack.

Hammer / Hammer (bouncing) Parameters:

•
•

The Mass knob adjusts the mass of the hammer.
The Stiffness knob adjusts the stiffness of the hammer’s surface area.

Plectrum Parameters:

•

•

The Protrusion knob adjusts how much of the plectrum’s surface area is placed under the string.
Lower values result in a “thinner,“ smaller sound, as there is less mass setting the string into
motion.
The Stiffness knob adjusts the stiffness of the plectrum.

Universal Exciter Parameters:

•
•

•

The Velocity knob adjusts the speed at which the exciter activates the string.
The Position knob specifies the point on the string where the exciter makes contact. At 0%, the
exciter contacts the string at its termination point, while at 50% it activates the string at its
midpoint. When the Fix. Pos switch (described in more detail below) is enabled, however, the
position is not dependent on the length of the string.
The Damping knob adjusts how much of the exciter’s impact force is absorbed back into the
exciter. Note: For the Hammer (bouncing) exciter, this is somewhat analogous to the Stiffness
parameter, but instead of controlling the stiffness of the hammer’s surface it adjusts the stiffness
of the virtual “spring“ that connects the hammer to the mass that powers it. As you increase the
Damping amount, the interaction between the hammer and string will become shorter,
generally resulting in a louder, brighter sound.

The Fix. Pos switch fixes the contact point to a single location, rather than changing as the length of the
string changes. This behavior is similar to that of a guitar, where the picking position is always
basically the same regardless of the notes being played. On a piano, the exciter position is relative —
the hammers normally strike the string at about 1/7th of their length — and so is best modeled with
Fix. Pos turned off.

Finally, the Vel and Key sliders allow you to modulate their behavior based on note velocity or pitch,
respectively.

Please note that the Exciter section’s parameters work closely together to influence the overall
behavior of the instrument. You may find that certain combinations of settings result in no sound at all.

28.12.2.4 The Damper Section

Tension’s Damper Section.

All string instruments employ some type of damping mechanism that mutes the resonating string. In
pianos, this is a felt pad that is applied to the string when the key is released. In instruments such as
guitars and violins, the player damps by stopping the string’s vibration with their fingers. Dampers
regulate the decay of strings but also produce some sound of their own, which is an important
characteristic of a string instrument’s timbre. The Damper section can be toggled on or off via the
switch next to its name.

Although a damper functions to mute the string rather than activate it, it is somewhat analogous to a
hammer, and shares some of the same parameters.

The Mass knob controls how hard the damper’s surface will press against the string. As you increase
the value, the string will mute more quickly.

The stiffness of the damper’s material is adjusted with the Stiffness control. Lower values simulate soft
materials such as felt, while higher values model a metal damper.

Note that very high Mass and Stiffness values can simulate dampers that connect with the string hard
enough to change its effective length, thus causing a change in tuning.

The Velocity control adjusts the speed with which the damper is applied to the string when the key is
released, as well as the speed with which it is lifted from the string when the key is depressed. Be
careful with this parameter — very high Velocity values can cause the damper to hit the string
extremely hard, which can result in a very loud sound on key release. Note that the state of the Gated
switch determines whether or not the Velocity control is enabled. When the Gated switch is turned on,

the damper is applied to the string when the key is released. With Gated off, the damper always
remains on the string, which means that the Velocity control has no effect.

The Position knob serves an analogous function to the control in the Exciter section, but here specifies
the point on the string where the damper makes contact. At 0%, the damper contacts the string at its
termination point, while at 50% it damps the string at its midpoint. The behavior is a bit different if the
Fix. Pos switch is enabled, however. In this case, the contact point is fixed to a single location, rather
than changing as the length of the string changes.

The Mass, Stiffness and Velocity, and Position parameters can be further modulated by note pitch
using the Key sliders below them.

The stiffness of the damper mechanism is adjusted with the Damping knob, which affects the overall
amount of vibration absorbed by the damper. Lower values result in less damping (longer decay
times). But this becomes a bit less predictable as the Damping value goes over 50%. At higher values,
the mechanism becomes so stiff that it bounces against the string. This in turn reduces the overall
amount of time that the damper is in contact with the string, causing an increase in decay time. The
best way to get a sense of how this parameter behaves is to gradually turn up the knob as you
repeatedly strike a single key.

The String Section

Tension’s String Section.

The vibration of the string is the main component of a stringed instrument’s sound. The effective length
of the string is also responsible for the pitch of the sound we hear.

The Decay slider determines how long it takes for the resonating string to decay to silence. Higher
values increase the decay time. The < Key slider next to Decay allows decay time to be modulated by
note pitch.

The Ratio slider sets the ratio of the decay time of the string’s oscillation during note onset and release.
At 0%, the time set by the Decay slider sets the decay time for both the onset and release of the note.
As you increase the Ratio, the release time decreases but the onset decay time stays the same.

The theoretical model of a resonating string is harmonic, meaning that the string’s partials are all exact
multiples of the fundamental frequency. Real-world strings, however, are all more or less inharmonic,
and this increases with the width of the string. The Inharm slider models this behavior, causing upper
partials to become increasingly out of tune as its value increases.

The Damping slider adjusts the amount of high frequency content in the string’s vibration. Higher
values result in more upper partials (less damping). This parameter can be modulated by note pitch
via the < Key slider to its right.

The Vibrato Section

Tension’s Vibrato Section.

The Vibrato section uses an LFO to modulate the string’s pitch. As with all of Tension’s parameters, the
controls in this section can be used to enhance the realism of a stringed instrument model — or to
create something never heard before.

The Vibrato section can be toggled on or off via the switch next to its name.

The Delay slider sets how long it will take for the vibrato to start after the note begins, while Attack sets
how long it takes for the vibrato to reach full intensity (as set by the Amount knob).

The two most important parameters in this section are the Rate and Amount sliders. Rate adjusts the
frequency of the pitch variation, while Amount adjusts the intensity (amplitude) of the effect.

The < Mod slider adjusts how much the modulation wheel will affect the vibrato intensity. This control is
relative to the value set by the Amount knob.

The Error slider introduces unpredictability into the vibrato, by introducing random deviation to the
Rate, Amount, Delay and Attack parameters.

28.12.2.5 The Termination Section

Tension’s Termination Section.

The Termination section models the interaction between the fret, finger and string. On a physical
instrument, this interaction is used to change the effective length of the string, which in turn sets the
pitch of the note played.

The Termination section can be toggled on or off via the switch next to its name.

The Finger Mass parameter can additionally be modulated by velocity or note pitch, via the Vel and
Key sliders.

The physical parameters of the finger are adjusted with the Finger Mass and Finger Stiff knobs, which
set the force the finger applies to the string and the finger’s stiffness, respectively. The stiffness of the
fret is modeled with the Fret Stiff parameter.

28.12.2.6 The Pickup Section

Tension’s Pickup Section.

The Pickup Section models the effect of an electromagnetic pickup, similar to the type found in an
electric guitar or electric piano. It can be toggled on or off via the switch next to its name. The only
control here is the Position slider, which functions similarly to this parameter in the Exciter and Damper
sections. At 0%, the pickup is located at the string’s termination point, while at 50% it is under the
midpoint of the string. Lower values generally result in a brighter, thinner sound, while higher values
have more fullness and depth.

The Body Section

Tension’s Body Section.

The role of the body or soundboard of a string instrument is to radiate the vibration energy from the
strings. The body also filters these vibrations, based on its size and shape. In some instruments, such as
guitars, the body also includes an air cavity which boosts low frequencies.

The Body section can be toggled on or off via the switch next to its name.

The Body Type chooser allows you to select from different body types modeled after physical
instruments.

The Body Size chooser sets the relative size of the resonant body, from extra small (XS) to extra large
(XL). In general, as you increase the body size, the frequency of the resonance will become lower.

The decay time of the body’s resonance can be adjusted with the Decay knob. Higher values mean a
longer decay.

The Str/Body knob adjusts the ratio between the String section’s direct output and the signal filtered
by the Body section. When turned all the way to the right, there is no direct output from the String
section. When turned all the way to the left, the Body section is effectively bypassed.

You can further modify the body’s frequency response with the Low Cut and High Cut knobs.

Tension’s Volume Knob.

The Volume knob to the right of the Body section sets the overall output of the instrument. This knob is
also accessible from the Filter/Global tab.

28.12.3 Filter/Global Tab

Tension’s Filter/Global Tab.

Tension’s Filter/Global tab features a polyphonic filter with envelope, LFO, and MIDI modulation
options, keyboard and portamento options, and an integrated Unison audio effect.

Tension’s Filter Section.

Tension’s Filter section features a highly configurable multi-mode filter that sits between the String and
Body sections. In addition, the filter can be modulated by a dedicated envelope generator and low-
frequency oscillator (LFO).

Note that the entire Filter section can be toggled on or off via the switch in the Filter subsection, while
the Filter Envelope and Filter LFO sections each have their own individual toggles.

The filter’s chooser allows you to select the filter type. You can choose between 2nd and 4th order
low-pass, band-pass, notch, high-pass and formant filters.

The resonance frequency of the filter is adjusted with the Freq slider, while the amount of resonance is
adjusted with the Res control. When a formant filter is selected, the Res control cycles between vowel
sounds. The Freq and Res controls can each be modulated by LFO, envelope or note pitch via the
sliders below. Note that the LFO and Env sliders have no effect unless the Envelope and LFO
subsections are enabled.

The Filter Envelope subsection can be toggled on or off via the switch next to its name. It is a standard
ADSR (attack, decay, sustain, release) with a few twists:

•

•

•

•

While the attack time is set with the Attack knob, this time can also be modulated by MIDI note
velocity via the Vel slider below the knob. As you increase the Vel value, the attack time will
become increasingly shorter at higher velocities.
The time it takes for the envelope to reach the sustain level after the attack phase is set by the
Decay knob.
The Sustain knob sets the level at which the envelope remains at the end of the decay phase
until the key is released. When this knob is turned all the way to the left, there is no sustain
phase. With it turned all the way to the right, there is no decay phase. The sustain level can be
additionally modulated by note velocity via the Vel slider below the knob. Higher values result
in an increased sustain level as the velocity increases.
The release time is set with the Release knob. This is the time it takes for the envelope to reach
zero after the key is released.

The Filter LFO subsection provides an additional modulation source for the filter. This section can be
toggled on or off via the switch next to its name.

The LFO waveform chooser sets the type of waveform used by the LFO. You can choose between sine,
triangle, rectangular and two types of random waveforms. The first random waveform steps between
random values while the second uses smoother ramps.

The LFO’s speed is set with the Rate knob. The switches below this knob toggle the Rate between
frequency in Hertz and tempo-synced beat divisions.

Lastly, the Attack knob controls how long it takes for the oscillator to reach its full amplitude while the
Delay knob controls how long it will take for the LFO to start after the note begins.

Tension’s MPE Section.

The MPE section includes mapping options for MPE pressure and slide data, as well as the option to
set Tension’s global and per-note pitch bend ranges. All three MPE sources include Activity LEDs,
which light up whenever Tension receives MPE signals.

For both the Pressure and Slide sources, you can choose two destinations where MPE data is routed,
and adjust the level of modulation using the Amount sliders.

Pitch Bend controls allow you to adjust the modulation range for global pitch bend, as well as the
MPE per-note pitch bend (Note PB) in semitones.

Tension’s Keyboard Section.

The Keyboard section contains all of Tension’s polyphony, tuning, MIDI parameters.

The Octave, Semi and Detune controls function as coarse and fine tuners. Octave transposes the entire
instrument by octaves, while Semi transposes up or down in semitone increments. The Detune slider
adjusts in increments of one cent (up to a maximum of 50 cents up or down).

The Voices chooser sets the available polyphony.

Stretch simulates a technique known as stretch tuning, which is a common tuning modification made to
electric and acoustic pianos. At 0%, Tension will play in equal temperament, which means that two
notes are an octave apart when the upper note’s fundamental pitch is exactly twice the lower note’s.
But because the actual resonance behavior of a vibrating tine or string differs from the theoretical

model, equal temperament tends to sound “wrong“ on pianos. Increasing the Stretch amount raises
the pitch of upper notes while lowering the pitch of lower ones. The result is a more brilliant sound.
Negative values simulate “negative“ stretch tuning; upper notes become flatter while lower notes
become sharper.

The Error slider increases the amount of random tuning error applied to each note. Try very high
values if you would like to relive your experiences from junior high school orchestra.

Lastly, Priority determines which notes will be cut off when the maximum polyphony is exceeded.
When Priority is set to High, new notes that are higher than currently sustained notes will have priority,
and notes will be cut off starting from the lowest pitch. Low Priority is the opposite. The Last setting
gives priority to the most recently played notes, cutting off the oldest notes as necessary.

Tension’s Portamento Section.

The Portamento section is used to make the pitch slide between notes rather than changing
immediately. The effect can be toggled on and off via the switch next to its name.

The Time slider sets the overall speed of the slide.

With Legato enabled, the sliding will only occur if the second note is played before the first note is
released.

Prop. (Proportional) causes the slide time to be proportional to the interval between the notes. Large
intervals will slide slower than small intervals. Disabling this switch causes the slide time to be constant
regardless of interval.

Tension’s Unison Section.

The Unison section allows you to stack multiple voices for each note played. Use the Unison toggle to
switch the section on or off.

The Voices switch selects between two or four stacked voices, while Detune adjusts the amount of
tuning variation applied to each stacked voice. Low values can create a subtle chorusing effect, while
high values provide another good way to approximate a youth orchestra.

Increasing the Delay amount adds lag before each stacked voice is activated.

Tension’s Volume Knob.

The Volume knob in the corner sets the overall output of the instrument. This knob is also accessible
from the String tab.

28.12.4 Sound Design Tips

At first glance, Tension’s modular architecture may not seem so different from what you’re used to in
other synthesizers; it consists of functional building blocks that feed information through a signal path
and modify it as it goes. But it’s important to remember that Tension’s components are not isolated from
one another; what you do to one parameter can have a dramatic effect on a parameter somewhere
else. Because of this, it’s very easy to find parameter combinations that produce no sound at all. It’s
also very easy to create extremely loud sounds, so be careful when setting levels!

When using Tension, it may help to think about the various sections as if they really are attached to a
single, physical object. For example, a bow moving at a slow speed could perhaps excite an
undamped string. But if that string is constricted by an enormous damper, the bow will need to
increase its velocity to have any effect.

To get a sense of what’s possible, it may help to study how the presets were made. You’ll soon realize
that Tension can do far more than just strings.

28.13 Wavetable

The Wavetable Instrument.

Wavetable is a synthesizer that combines two wavetable-based oscillators, two analog-modelled
filters, and a powerful but intuitive modulation system. It’s designed to be usable by musicians and
sound designers with any amount of synthesis experience; it’s simple enough to yield great results with
a minimum of effort but offers a nearly limitless range of possibilities as you go deeper.

Wavetable’s interface is divided into three main sections: the oscillators (which each have their own
tab), the two filters, and the modulation section (which is divided between three tabs). To see more
parameters in a single view, click the
the main Device View and the expanded view depending on the dimensions of your screen layout.

 button in Wavetable’s title bar. Parameters will move between

28.13.1 Wavetable Synthesis

Wavetable’s oscillators produce sound using a technique called wavetable synthesis. A wavetable is
simply an arbitrary collection of short, looping samples that are arranged together. Playing a note
with the oscillator fixed to just one of these samples will produce a steady tone with a consistent
timbre. But the real power of wavetable synthesis comes by moving between the various samples in
the table as the note plays, which results in a shifting timbre. Wavetable synthesis is extremely well-
suited for producing dynamic sounds that change over time.

28.13.2 Oscillators

Wavetable’s oscillators have been optimized for maximum sound quality. As long as no modulation is
applied, the raw output of the oscillators is perfectly band-limited and will not produce aliasing
artifacts at any pitch.

Wavetable’s Oscillators.

Each oscillator can be turned on or off independently via a switch in the oscillator’s tab. Clicking a tab
will select that oscillator, revealing its parameters for editing.

The overall output level of each oscillator is adjusted with its Gain slider, while its position in the stereo
field can be adjusted with the Pan control. The coarse and fine tuning of each oscillator can be set
with the Semi and Detune controls. Note that this tuning is in relation to the global Transposition slider.

Select a wavetable using the choosers or the arrow buttons. The first chooser selects a category of
wavetable, while the second chooser selects a specific wavetable from within that category. The
arrow buttons will automatically switch to the next category when you reach the end of the current
one, so you can continuously move through the wavetables using the arrows alone.

You can extend the sonic capabilities of Wavetable’s oscillator section by loading any WAV or AIFF
file as a wavetable. To do this, drag and drop a sample from the browser directly onto the wavetable
visualization. The choosers and arrow buttons will now reference the folder containing the imported
sample, allowing you to quickly audition any other samples in that folder.

Wavetable will automatically process imported samples to reduce unwanted artefacts. Note that you
can bypass this processing by activating the Raw mode switch. Raw mode is especially useful when
loading files that have been prepared specifically for use as a wavetable. However, it can also be
“misused” to create unpredictable, noisy or glitchy sounds.

Wavetable’s Raw Mode Switch.

The oscillator’s wavetable is visualized in the center of the oscillator tab. Clicking and dragging within
the visualization will move to a different position within the wavetable. You can also change the
wavetable position via the Wave Position slider.

There are two types of wavetable visualizations available, and these can be switched via the
wavetable visualization switch. Both views represent the same information, but visualized in different
ways. The linear view arranges the waveforms from bottom to top, with time running from left to right.
The polar view displays the waveforms as loops from inside to outside, with time running clockwise.

Although there is a huge range of available wavetables, it’s also possible to transform the sound of
each wavetable itself through the use of oscillator effects. Select from three effects in the chooser and
then adjust the parameters for those effects via the sliders to the right. The oscillator effects include:

•

•

•

FM — Applies frequency modulation to the oscillator. The Amt slider adjusts the intensity of the
frequency modulation, while the Tune slider determines the frequency of the modulation
oscillator. With a tuning of 50% (and -50%), the modulation oscillator is one octave higher (or
lower) than the main oscillator. At 100% (and -100%), the modulation oscillator is two octaves
higher (or lower). In between these values, the modulation oscillator is at inharmonic ratios,
which is ideal for creating noisy overtones.
Classic — Provides two modulation types that are common from classic analog synthesizers.
PW adjusts the pulse width of the waveform. Note that in hardware synthesizers, it is normally
only possible to adjust the pulse width of square waves. In Wavetable, the pulse width can be
adjusted for all wavetables. Sync applies a “hidden” oscillator that resets the phase of the
audible oscillator, altering its timbre.
Modern — Provides two additional options for distorting the shape of the waveform. Warp is
similar to pulse width, while Fold applies wavefolding distortion.

Note that the values of the two effects parameters don’t change when the effect type changes. This
makes it possible to move between the effects to experiment with how the different processes affect
the timbre with the same values.

28.13.3 Sub Oscillator

Wavetable’s Sub Oscillator.

In addition to the two main oscillators, Wavetable includes a sub oscillator. This can be toggled on or
off using the Sub toggle, and its output level is adjusted with the Gain knob.

The Tone control alters the timbre of the sub oscillator. At 0%, the oscillator produces a pure sine wave.
Turning Tone up increases the harmonic content of the waveform.

The tuning of the sub is determined by the played note and the global Transpose value, but you can
shift the sub down by one or two octaves using the Octave switches.

28.13.4 Filters

Wavetable’s filters can be very useful for shaping the sonically rich timbres created by the oscillators
and their effects. And, since the oscillators also provide you with the classic waveforms of analog
synthesizers, you can very easily build a subtractive-style synthesizer with them.

Wavetable’s Filters.

Wavetable offers a variety of filter types including low-pass, high-pass, band-pass, notch, and a
special Morph filter. Each filter can be switched between 12 and 24 dB slopes as well as a selection
of analog-modeled circuit behaviors developed in conjunction with Cytomic that emulate hardware
filters found on some classic analog synthesizers.

The Clean circuit option is a high-quality, CPU-efficient design that is the same as the filters used in EQ
Eight. This is available for all of the filter types.

The OSR circuit option is a state-variable type with resonance limited by a unique hard-clipping
diode. This is modeled on the filters used in a somewhat rare British monosynth, and is available for all
filter types.

The MS2 circuit option uses a Sallen-Key design and soft clipping to limit resonance. It is modeled on
the filters used in a famous semi-modular Japanese monosynth and is available for the low-pass and
high-pass filters.

The SMP circuit is a custom design not based on any particular hardware. It shares characteristics of
both the MS2 and PRD circuits and is available for the low-pass and high-pass filters.

The PRD circuit uses a ladder design and has no explicit resonance limiting. It is modeled on the filters
used in a legacy dual-oscillator monosynth from the United States and is available for the low-pass
and high-pass filters.

The most important filter parameters are the typical synth controls Frequency and Resonance.
Frequency determines where in the harmonic spectrum the filter is applied; Resonance boosts
frequencies near that point. Note that you can adjust the Frequency and Resonance parameters by
clicking and dragging either of the filter dots in the filter display.

When using the low-pass, high-pass, or band-pass filter with any circuit type besides Clean, there is
an additional Drive control that can be used to add gain or distortion to the signal before it enters the
filter.

The Morph filter has an additional Morph control which sweeps the filter type continuously from low-
pass to band-pass to high-pass to notch and back to low-pass.

Filter routing allows you to arrange the filters in various configurations for drastically different sculpting
techniques. You can choose from one of three different routings:

•

•

Serial — Routes all oscillators into Filter 1, and routes Filter 1 into Filter 2. Sub is routed to both
filters.
Parallel — Routes the two main oscillators into Filter 1 and Filter 2. Sub is routed to both filters.

•

Split — Routes Oscillator 1 to Filter 1, and Oscillator 2 to Filter 2. Sub is split in half and sent to
both filters. If either filter is off, the corresponding oscillator’s signal is still audible. Split can be
used to treat each filter separately, and is useful for cases where you want to create layered
synth sounds. If the main oscillators are disabled while both filters are engaged, Split can also
be used to add extra treatment to the Sub oscillator.

28.13.5 Matrix Tab

The Modulation Matrix enables assigning modulation from Envelopes and LFOs (also known as
“internal modulation sources”) to parameters within the instrument (or “modulation targets”).

Wavetable’s Matrix Tab.

The modulation sources run horizontally, while the modulation targets run vertically. Click and drag
within the grid to change the amount of modulation that the selected source applies to the selected
parameter.

Note that certain parameters are additive modulation targets, while others are multiplicative
modulation targets.

Additive modulation is applied to a parameter using the following formula:

1.
2.

The outputs of a parameter’s modulation sources are summed together.
The summed modulation value is added to the current parameter value.

Modulation values for additive modulation are centered around 0, with 0 being the “neutral” value.
Additive modulation values can be negative or positive. Modulation sources that output negative and
positive values are “bipolar” sources. Modulation sources that only output positive values are
“unipolar” sources.

Multiplicative modulation is applied to a parameter using the following formula:

1.
2.

The outputs of a parameter’s modulation sources are multiplied together.
The multiplied modulation value is multiplied with the current parameter value.

The neutral value for multiplicative modulation is 1, and the minimum value is 0. Parameters with
multiplicative modulation are noted throughout the Wavetable manual.

Click on a parameter in the instrument to make it appear temporarily in the matrix. If you apply
modulation to this parameter, it will remain in the matrix. If no modulation is applied, the parameter
will disappear from the matrix when you click another parameter. Note that the Matrix tab and MIDI
tab share the same rows.

Click on any of the modulation source headers located above the matrix to quickly jump to its
respective panel within the Mod Sources tab.

The Time slider will scale the times of all the modulators. Negative values will make envelopes and
LFOs faster, while positive values will make them slower. Modulating this value with an envelope or
LFO will not affect the assigned modulator, but that modulator will still scale to other destinations.

The Amount slider sets the overall amount of modulation for all sources in the modulation matrix. Note
that this is a multiplicative modulation destination.

28.13.6 Mod Sources Tab

The Mod Sources tab allows you to adjust Envelope and LFO settings, which are described in more
detail below.

Wavetable’s Mod Sources Tab.

Envelopes

Wavetable’s envelopes (Amp, Env 2 and Env 3) can be modified using Time and Slope parameters,
while Env 2 and Env 3 include additional Value controls. Note that you can adjust the Time, Slope
and Value parameters by clicking and dragging the envelope display.

Attack sets the time needed to travel from the initial value to the Peak value. The shape of this stage of
the envelope is determined by the Attack Slope value.

Decay sets the time needed to travel from the Peak value to the Sustain level. The shape of this stage of
the envelope is determined by the Decay Slope value.

Sustain sets the level reached at the end of the Decay stage. The envelope will remain at this level until
a Note Off occurs, unless the Loop mode is set to Trigger or Loop, in which case it will continue to the
Release stage as soon as it is reached. Note that this is a multiplicative modulation destination.

Release sets the time needed to travel to the Final value after a Note Off occurs. The shape of this
stage of the envelope is determined by the Release Slope value.

As mentioned above, Wavetable’s envelopes also provide parameters that adjust the slope of their
envelope segments. Positive slope values cause the envelope to move quickly at the beginning, then
slower. Negative slope values cause the envelope to remain flat for longer, then move faster at the
end. A slope of zero is linear; the envelope will move at the same rate throughout the segment.

The Initial slider sets the starting value of the envelope when it is triggered. Note that this is a
multiplicative modulation destination. This control is not available for the amp envelope.

The Peak slider sets the value which marks the end of the Attack stage and the beginning of the Decay
stage. This control is not available for the amp envelope.

The Final slider sets the value at the end of the Release stage. This control is not available for the amp
envelope.

The Loop Modes drop-down lets you choose from one of three modes:

•
•
•

None will hold the Sustain portion until a Note Off, and will not loop.
Trigger will play all segments once a Note On is received.
Loop will loop the entire envelope without holding the Sustain, until the voice ends.

28.13.6.1 LFOs

Wavetable includes two LFOs, which can be adjusted individually via the parameters described in this
section.

Wavetable’s LFOs.

You can choose from one of five LFO waveforms, and use the Shape slider to modify the selected
waveform’s shape:

•
•
•
•

Sine and Saw: Applies an increasing or decreasing slope.
Triangle: Morphs the symmetry from Ramp to Saw, with Triangle in the middle.
Square: Changes the pulse width.
Random: Changes the distribution of extreme values.

The Sync switch sets the LFO Rate in Hertz or synced to the song tempo, while the Rate slider sets the
LFO frequency in Hertz or beat divisions. Note that you can also adjust the LFO frequency by
dragging the waveform display.

Amount adjusts the amount of LFO modulation that is applied to incoming signals. Note that this is a
multiplicative modulation destination.

The Offset slider offsets the phase of the LFO so that it starts at a different value. Note that Offset
cannot be modulated.

You can use the LFO Attack slider to adjust the time the LFO takes to fade in, when it has been
triggered by a Note On.

When enabled, the LFO Retrigger switch will cause the LFO to reset to its starting point, or initial
phase, on each new MIDI note. This can create hybrid LFO shapes if the LFO is retriggered before
completing a cycle.

28.13.7 MIDI Tab

Assigning MIDI to parameters can turn Wavetable into a dynamic performance instrument. Within the
MIDI Modulation Matrix, MIDI modulation sources can be assigned to multiple parameters within the
instrument (or “modulation targets”).

Wavetable’s MIDI Tab.

When Velocity is assigned, Wavetable will use the incoming MIDI note’s velocity value to modulate
target parameters for the duration of that note.

When Note is assigned, Wavetable will use the incoming MIDI note’s pitch to modulate target
parameters for the duration of that note. The pitch modulation range is centered around C3. This
means when it is assigned to Filter Frequency with the modulation amount set to 100%, the filter will
precisely track the played note.

Pitch Bend, Aftertouch and Modulation Wheel: these are hardware controls found on many MIDI
controller devices. If you do not have such a device, you can still modulate the parameters with clip
envelopes.

When Random is assigned, Wavetable will modulate target parameters by a random value, which is
calculated each time a note is triggered.

Click on a parameter in the instrument to make it appear temporarily in the matrix. If you apply
modulation to this parameter, it will remain in the matrix. If no modulation is applied, the parameter
will disappear from the matrix when you click another parameter. Note that the Matrix tab and MIDI
tab share the same rows.

28.13.8 Global and Unison Controls

Wavetable’s global controls affect the overall behavior and performance of the instrument.

Wavetable’s Global Controls.

Transpose adjusts the relative pitch of the Wavetable instrument in semitones.

Volume adjusts the overall level of the instrument. Note that is a multiplicative modulation destination.

The Poly/Mono toggle switches the instrument between a single voice with legato envelopes (Mono)
and a polyphonic instrument (Poly).

The Poly Voices drop-down menu lets you set the maximum number of notes that can sound
simultaneously. Note that Poly Voices is only active when the Poly/Mono switch is set to Poly.

Glide adjusts the time overlapping notes take to slide their pitch to the next incoming pitch. Note that
Glide is only active when the Poly/Mono switch is set to Mono.

The Unison drop-down menu lets you choose from one of six unison modes (or none). Unison modes
use multiple oscillators with different phases, stereo locations, or wavetable positions to provide a
fuller sound.

•

•

•

•

•

•

Classic: The oscillators are detuned with equal spacing and panned to alternating stereo
channels.
Shimmer: The oscillator pitches are jittered at random intervals, giving a shimmering reverb-like
effect. A small amount of wavetable offset is also applied for extra fullness.
Noise: Pitches are jittered as in the Shimmer unison mode, but at a much faster rate, resulting in
noisy breathy textures. A small amount of wavetable offset is applied for extra fullness.
Phase Sync: The oscillators are detuned as in Classic unison mode, but the phases are synced
when a note is started giving a strong sweeping phaser-style effect.
Position spread: The wavetable positions for each oscillator are evenly spread out by an
amount. A small amount of detune is additionally applied for extra width.
Random note: The wavetable positions and detune amount for each oscillator are randomised
each time a note is started.

The Voices slider sets the number of simultaneously running oscillators per wavetable oscillator. More
voices will result in a thicker sound, whereas less voices will sound clearer.

The Amount slider adjusts the intensity of the unison effect, and has different behavior in each unison
mode. Note that this is a multiplicative modulation destination.

28.13.9 Hi-Quality Mode

Wavetable’s Hi-Quality Option.

You can toggle on Hi-Quality mode on or off from Wavetable’s context menu.

When Hi-Quality is off, Wavetable modulation is calculated every 32 samples. Low-power versions
of the Cytomic filters are also used to further reduce CPU.

Using Wavetable with Hi-Quality mode off can save up to 25% CPU compared to having it enabled,
which is ideal for working with large sets or maintaining low latencies.

As of Live 11.1, Hi-Quality mode will be off by default when loading a new instance of Wavetable or
any of its Core Library presets. However, any user presets or Live Sets created previously will still load
Wavetable in Hi-Quality mode to ensure sound consistency with earlier Live versions.

Note: Subtle sound differences may occur when Hi-Quality mode is enabled.

29. Max for Live

Max for Live, an add-on product co-developed with Cycling ’74, allows users to extend and
customize Live by creating instruments, audio and MIDI effects, as well as MIDI Tools. Max for Live
can also be used to extend the functionality of hardware controllers and even modify clips and
parameters within a Live Set.

In addition to providing a comprehensive toolkit for building devices, Max for Live also comes with a
collection of pre-made instruments, effects, MIDI Tools and tutorials. These can be used just like Live’s
built-in devices and can also give you ideas for your own device building projects.

29.1 Setting Up Max for Live

Max for Live comes pre-installed with Live Suite, as well as Standard when using the Max for Live
add-on, and does not require any additional setup.

However, if you prefer to use an external Max installation, you will first need to point to it in Live’s File
& Folder Settings:

The Path to the Max Installation.

Once Live has found the external Max application, Max for Live should be ready for use. At this point,
the Max content will begin to install into your Live Library.

29.2 Using Max for Live Devices

Max for Live comes with a collection of instruments, effects and MIDI Tools which are ready for use. A
selection of Max for Live devices from Live’s Core Library can be found in the Instruments, Audio
Effects and MIDI Effects labels within the browser. Additional Max for Live devices as well as Max for
Live MIDI Tools appear in the Max for Live label in the browser.

Many of these devices also come with their own presets, which are similar to Live’s device presets but
with one important difference: because a Max device can be stored outside of Live’s known locations,
it is important to make sure that any presets that refer to this device remain associated with it.

If you save a preset for a Max device, Live will try to maintain the necessary file references by
copying the Max device into your User Library and saving the preset based on this copy. If the
referenced Max file is then moved or renamed, however, these file associations may be broken. If this
happens, you can use Live’s File Manager to fix the problem.

To avoid these issues, we recommend always storing Max devices and their presets in your User
Library. Note that this is the default location that is suggested when pressing the Save Preset button in
the title bar of the Max device.

29.3 Editing Max for Live Devices

Max devices (or “patches“) are constructed of objects that send data to each other via virtual cables.
An empty Max Audio Effect, for example, already contains some of these elements: the plugin~ object
passes all incoming audio to the plugout~ object, which then passes the audio on to any additional
devices in the chain.

A Default Max Audio Effect.

To load an empty Max device, drag a Max Instrument, Max MIDI Effect or Max Audio Effect from the
browser into your Set.

What a Max device actually does depends on the objects that it contains, and the way in which
they’re connected together. The area where you work with Max objects is called the editor (or
“patcher“), and can be accessed by pressing the Edit button in the Max device’s title bar.

The Edit Button for a Max Device.

This launches the Max editor in a new window, with the current device loaded and ready for editing.

A Default Max Audio Effect in the Patcher.

After editing, you should save your Max device before you use it in Live. This is done via the Save or
Save As commands in Max’s File menu. Saving an edited device will automatically update all
instances of that device that are used in your current Live Set. If you choose Save As, you will be
asked whether or not the new version should update only the device that was originally opened for
editing or all instances of the device in the Set.

The default location when saving a Max device is the folder in the Library that corresponds to the type
of device being saved. We recommend always saving Max devices to this default location.

Unlike Live’s native devices, Max devices are not saved inside Live Sets, but rather as separate files.

29.4 Building Max for Live MIDI Tools

You can create your own Max for Live MIDI Tools in two ways:

1.

2.

By using the Max MIDI Transformation or Generator template included in the Transformation
and Generative Tools tabs/panels respectively.
By editing an existing Max for Live MIDI Tool.

Building a Max for Live MIDI Tool follows the same principles as building other Max for Live devices:
with a Max MIDI Transformation/Generator template or an existing Max for Live MIDI Tool selected,
click on the Edit button to launch the Max editor (“patcher”).

The Edit Button in a Max MIDI Transformation.

When you are done editing, use the Save or Save As commands in the patcher’s File menu to save the
Max for Live MIDI Tool.

By default, Max for Live MIDI Tools are saved to these folders on your computer:

•
•

Transformations: ~/Music/Ableton/User Library/MIDI Tools/Max Transformations
Generators: ~/Music/Ableton/User Library/MIDI Tools/Max Generators

Alternatively, any folder within Places in Live’s browser can be used to store the MIDI Tools’ AMXD
files. For example, you could create a new folder called “My Favorite MIDI Tools” and save the Max
for Live MIDI Tools you have built within this folder. Then when you add the folder to Places in Live,
these MIDI Tools will appear in the drop-down menus in the Transformation/Generative Tools tabs/
panels.

Note that if Max for Live MIDI Tools are not saved to the default location or within Live’s Places, they
will not be found by Live’s Indexer, and therefore will not appear in the Clip View’s Transformation/
Generative Tools tabs/panels.

For more information on the Max objects used for creating Max for Live MIDI Tools, as well as a
walkthrough of patching a Max for Live Transformation or Generator, please refer to the Max for Live
MIDI Tools guide, accessible via the Max documentation. In a Max window, select Reference from
the Help Menu, navigate to the Max for Live category and then Guides.

29.5 Max Dependencies

As mentioned earlier, there are some special file management considerations when creating presets
for Max devices. Additionally, Max devices themselves may depend on other files (such as samples,
pictures, or even other Max patches) in order to work properly. Max for Live helps to deal with
external dependencies by allowing you to freeze a Max device. A frozen device contains all of the
files that are needed to use it.

Note that freezing of Max devices is not the same as Live’s Freeze Track command.

To learn more about freezing, and about how Max deals with managing dependencies for its own
files, we recommend reading the built-in Max documentation.

29.6 Learning Max Programming

To help you learn more about building and editing Max devices, Cycling ’74 provides comprehensive
documentation and tutorials built into the Max environment. To access this documentation, select
“Reference“ from the Help menu in any Max window. There is also a Max for Live section within the
documentation contents.

You can also read the Max for Live Production Guidelines documentation on GitHub.

For hands-on learning, we suggest downloading the Building Max Devices Pack, which contains in-
depth lessons that cover all the steps you need to build your own Max tools.

Additionally, you can check out the Learn Max page from Cycling ’74 for a comprehensive collection
of learning resources.

30. Max for Live Devices

Live comes with a selection of custom-designed, built-in Max for Live devices. These devices include
instruments, effects, and MIDI Tools.

Because Max for Live devices are based on Max, you can edit and customize them in the Max editor
— unlike native Live devices. You can read more about this in the Max for Live chapter.

To learn the basics of using devices in Live, check out the Working with Instruments and Effects
chapter.

Note that different editions of Live have different feature sets, so some devices covered in this
reference may not be available in all editions.

30.1 Max for Live Instruments

30.1.1 DS Clang

The DS Clang Instrument.

DS Clang consists of two separate tones, white noise and a filter, allowing you to create a variety of
cowbell, clave and noise percussion sounds.

The Tone A/B sliders let you set the volume for each cowbell tone independently.

The Filter control sets the high-pass and band-pass filter cutoff, allowing you to change the color of
the sound. At higher values, the signal has more high-frequency content.

The Noise slider allows you to set the amount of white noise applied to the signal.

When the Clave switch is activated, you can add repeats to the clave sound using the Repeat slider.

You can use the Pitch parameter to change the pitch of the instrument. The Decay knob sets the length
of the sound, while the Volume control adjusts the overall level of the instrument.

To preview the sound of the instrument with its current settings, click anywhere in the upper half of the
display.

30.1.2 DS Clap

The DS Clap Instrument.

DS Clap is a mix of filtered noise and an impulse running through panned delay lines, that allows you
to create a range of sounds from a tight electronic clap to a more organic, humanized handclap.

The Sloppy control adjusts the delay time between the two delay lines, so you can set how tightly or
loose the panned claps play together. Tail adds filtered noise to the impulse of the clap.

The Spread slider sets the stereo width of the clap. 0% yields a mono signal while 100% creates a
widened stereo image. The Tone slider adjusts the color of the clap. At higher values, the signal has
more high-frequency content.

You can use the Tune parameter to change the pitch of the clap. The Decay knob sets the length of the
clap, while the Volume control adjusts the overall level of the instrument.

To preview the sound of the instrument with its current settings, click anywhere in the upper half of the
display.

30.1.3 DS Cymbal

The DS Cymbal Instrument.

DS Cymbal combines sine and pulse waveforms with high-passed noise, making it possible to
recreate a variety of timbres, from a thin ride cymbal to a heavy crash.

The Tone slider in the display sets the high-pass filter cutoff, allowing you to change the color of the
cymbal. At higher values, the signal has more high-frequency content.

You can use the Pitch parameter to change the pitch of the cymbal. The Decay knob sets the length of
the cymbal, while the Volume control adjusts the overall level of the instrument.

To preview the sound of the instrument with its current settings, click anywhere in the upper half of the
display.

30.1.4 DS FM

The DS FM Instrument.

Inspired by a classic Japanese FM synthesizer, DS FM lets you create a variety of effects, from static
bursts to metallic lasers.

The Tone slider in the display sets the low-pass filter cutoff, allowing you to change the color of the
drum. At higher values, the signal has more high-frequency content.

Feedb. adjusts the amount of feedback applied to the FM algorithm. Greater values yield more noise.

Amnt sets the amount of FM modulation, while the Mod slider blends between different modulation
types.

The Pitch parameter provides global pitch control. The Decay knob sets the length of the drum, while
the Volume control adjusts the overall level of the instrument.

To preview the sound of the instrument with its current settings, click anywhere in the upper half of the
display.

30.1.5 DS HH

The DS HH Instrument.

DS HH is a blend of noise and sine waveforms, with which you can produce any number of sounds,
from sharp closed hats to sizzling open hats.

The Noise toggle lets you choose between two noise types: white or pink.

The Tone slider in the display sets the high-pass filter cutoff, allowing you to change the color of the
hat. At higher values, the signal has more high-frequency content.

The pitched portion of the sound is filtered through a resonant high-pass filter. The filter can be
switched between 12 and 24 dB slopes, and the attack time can be set via the Attack slider.

You can use the Pitch parameter for global pitch control. The Decay knob sets the length of the hat,
while the Volume control adjusts the overall level of the instrument.

To preview the sound of the instrument with its current settings, click anywhere in the upper half of the
display.

30.1.6 DS Kick

The DS Kick Instrument.

DS Kick is a kick drum synth with a modulated sine wave.

The Pitch slider lets you tune the kick in Hz. You can shape the kick sound by adding distortion via the
Drive slider, or adding harmonics using the OT slider.

The Attack parameter smooths the sound of the sine wave. The Click switch adds a click sound to the
kick, creating a sharper transient.

The Decay knob sets the length of the kick. Env can be used to set the pitch modulation. The Volume
control adjusts the overall level of the instrument.

To preview the sound of the instrument with its current settings, click anywhere in the upper half of the
display.

30.1.7 DS Sampler

The DS Sampler Instrument.

DS Sampler makes use of your own samples to create a drum synth module.

You can load a sample by dragging and dropping it onto the upper half of the display. The Start
control adjusts the position of the sample start, while the Length slider sets the sample playback length.

You can use the Tune slider to tune your sample by +/- 48 semitones. The Loop switch toggles the
sample loop on and off.

The Decay knob sets the decay time of the sample’s amplitude. The Shaper parameter adds distortion
to produce a punchy and gritty sound. The Volume control adjusts the overall level of the instrument.

30.1.8 DS Snare

The DS Snare Instrument.

DS Snare consists of a pitched oscillator and noise, providing a snare palette ranging from a
traditional acoustic snare sound, to the gated noise snare often heard in electronic dance music.

The Color parameter controls the tone of the pitched signal, while the Tone parameter controls the
presence of the noise signal.

You can apply one of three different filter types to the noise signal: low-pass, high-pass, or band-pass.

The Decay knob sets the length of the snare, while the Tune parameter provides global pitch control.
The Volume control adjusts the overall level of the instrument.

To preview the sound of the instrument with its current settings, click anywhere in the upper half of the
display.

30.1.9 DS Tom

The DS Tom Instrument.

DS Tom combines an impulse with various pitched oscillator waveforms, allowing you to synthesize
toms with various timbral qualities, from deep and thunderous to sharp and tappy.

You can use the Pitch slider to tune the tom in Hz. The Color parameter controls the filter gain and
cutoff, while the Tone slider controls the level of resonant band-pass filters to mimic the tuning of the
drum membrane.

The Bend parameter adjusts the pitch envelope. The Decay knob sets the length of the tom, while the
Volume control adjusts the overall level of the instrument.

To preview the sound of the instrument with its current settings, click anywhere in the upper half of the
display.

30.2 Max for Live Audio Effects

30.2.1 Align Delay

The Align Delay Effect

Align Delay is a utility delay for incoming signals that can be set in samples, milliseconds, or meters/
feet.

Using the Delay Mode drop-down menu, you can choose between three delay modes: Time,
Samples, and Distance.

Time mode sets the delay in milliseconds and can be used to adjust time between lasers and AV work,
or as a subtle stereo maker.

Samples mode sets the delay in samples and can be used to compensate for latency introduced by
other devices.

Distance mode sets the delay in meters or feet, either option can be toggled by using the m/ft button
next to the left and right delay sliders. Distance mode can be used to adjust PA system alignment or
monitor to main PA alignment.

You will also see a Celsius/Fahrenheit Temperature option in Distance mode. Matching the
temperature setting to the current temperature in the room you are using Align Delay in allows for
more precise delay adjustment as the sound will travel differently in warm and cold environments.

With Stereo Link engaged, the left channel’s settings are applied to the right channel and the right
channel will appear greyed out. Changing the settings for the left channel will apply the changes to
both sides.

30.2.2 Envelope Follower

The Envelope Follower Effect.

Envelope Follower uses a well-known technique which involves capturing a signal, smoothing and
reshaping its amplitude course in order to obtain a more or less continuous curve, and finally mapping
the curve to one or more control parameters. The “auto-wah” effect is perhaps the most well-known
application of the envelope following technique.

Activate the Map switch and click on a parameter in Live to assign that parameter as a mapping
target. To assign an additional mapping target, click on the button at the top-right of the display, click
any of the unassigned Map switches and click on another parameter in Live. A total of eight
parameters can be assigned. To unassign a parameter, click on the button to the right of its Map
switch. For each modulated parameter, the Min and Max sliders let you scale the resulting output
range after the modulation is applied.

You can use the Gain knob to set the gain applied to the incoming signal.

The Rise parameter smooths the attack of the envelope, while the Fall control smooths the release of
the envelope.

The Delay control sets the delay time of the envelope. The switches to the right of the Delay control
toggle the delay mode between time-based and tempo-synced beat divisions.

30.2.3 LFO

The LFO Effect.

LFO is a parameter modulation LFO for Live-specific parameters and third party plug-in parameters.

Activate the Map switch and click on a parameter in Live to assign that parameter as a mapping
target. To assign an additional mapping target, click on the button at the top-right of the display, click
any of the unassigned Map switches and click on another parameter in Live. A total of eight
parameters can be assigned. To unassign a parameter, click on the button to the right of its Map
switch. For each modulated parameter, the Min and Max sliders let you scale the resulting output
range after the modulation is applied.

You can choose from one of seven different waveforms: sine, sawtooth up, sawtooth down, triangle,
rectangle, random and binary noise.

The Jitter slider adds randomness to the waveform, while the Smooth control smooths value changes.

The Rate control specifies the LFO speed. The switches to the right of the Rate control toggle between
frequency in Hertz and tempo-synced beat divisions.

Depth sets the overall intensity of the LFO. Offset changes the starting point, or initial phase of an LFO,
so that it begins at a different point in its cycle.

The phase of the oscillator can be shifted using the Phase control.

To hold the current output value, activate the Hold switch.

You can click the R (Retrigger) button to re-trigger the phase of the LFO.

30.2.4 Shaper

The Shaper Effect.

Shaper is a multi-breakpoint envelope which generates modulation data for musical expression.

Activate the Map switch and click on a parameter in Live to assign that parameter as a mapping
target. To assign an additional mapping target, click on the button at the top-right of the display, click
any of the unassigned Map switches and click on another parameter in Live. A total of eight
parameters can be assigned. To unassign a parameter, click on the button to the right of its Map
switch. For each modulated parameter, the Min and Max sliders let you scale the resulting output
range after the modulation is applied.

You can create a breakpoint by clicking anywhere in the display. You can also delete a breakpoint by
Shift -clicking on it. Hold down the Alt (Win) / Option (Mac) key while dragging to create
curved segments.

To clear the display, press the Clear button in the bottom left corner. To the right of the Clear button,
you can choose from one of six breakpoint presets.

You can adjust the size of the grid via the Grid slider. When Snap is enabled, all breakpoints that you
create or reposition will snap to grid lines.

The smaller display on the top right provides an oscilloscope-style view of the output signal. The Jitter
slider adds randomness to the waveform, while the Smooth control smooths value changes.

The Rate control specifies the LFO speed. The switches to the right of the Rate control toggle between
frequency in Hertz and tempo-synced beat divisions.

Depth sets the overall intensity of the LFO. The phase of the oscillator can be shifted using the Phase
control.

You can click the R (Retrigger) button to re-trigger the phase of the LFO. Note that re-trigger is not
available if the Rate control is set to Sync mode.

Offset changes the starting point, or initial phase of an LFO, so that it begins at a different point in its
cycle.

30.3 Max for Live MIDI Effects

30.3.1 Envelope MIDI

The Envelope MIDI Effect.

Envelope MIDI is an ADSR device that you can control any Live parameter with.

Activate the Map switch and click on a parameter in Live to assign that parameter as a mapping
target. To assign an additional mapping target, click on the button at the top-right of the display, click
any of the unassigned Map switches and click on another parameter in Live. A total of eight
parameters can be assigned. To unassign a parameter, click on the button to the right of its Map
switch. For each modulated parameter, the Min and Max sliders let you scale the resulting output
range after the modulation is applied.

The Loop Mode drop-down lets you choose from one of four loop modes:

•
•

•

Free: The trigger rate is unaffected.
Sync: The trigger rate is defined by the song tempo. When Sync mode is active, you can set the
trigger rate via the Sync Rate drop-down.
Loop: The trigger rate is defined by the envelope time.

•

Echo: This creates repetitions of the original envelope. When Echo is active, you can adjust the
Envelope Echo Time and amount of Envelope Echo Feedback.

The Time slider sets the global envelope time.

When the Velocity switch is enabled, the envelope is modulated by note velocity. The Amount control
determines the intensity of the modulation.

The Attack control sets the attack time of the envelope. The Attack Slope slider adjusts the shape of the
Attack envelope segment.

The Decay control sets the decay time of the envelope. The Decay Slope slider adjusts the shape of the
Decay envelope segment.

The Sustain control sets the level reached at the end of the Decay stage. The Sustain Mode switch
toggles the Sustain function on or off.

The Release control sets the release time of the envelope. The Release Slope slider adjusts the shape of
the Release envelope segment.

You can adjust the Attack, Decay, Sustain and Release parameters by clicking and dragging the
envelope display.

30.3.2 Expression Control

The Expression Control Effect.

Expression Control is a MIDI effect that lets you control, transform, and map MIDI and MPE
expression data. This version of Expression Control is a new take on the Max for Live device of the
same name, with expanded functionality and a redesigned user interface centered around a visual
display of the device’s modulation curves.

The previous version of this device is still available and has been renamed Expression Control Legacy.
Live Sets made in Live 11 that contain Expression Control will load the Expression Control Legacy
device automatically.

Expression Control has five Mod Source Tabs that can be used to set a MIDI or MPE expression
parameter as a modulation source. A MIDI Input Source drop-down menu in each tab lets you
choose between ten expression parameters: Velocity, Modwheel, Pitchbend, Pressure, Keytrack,
Expression, Random, Increment, Slide, and Sustain.

Clicking on the Map to Target button links the selected modulation source to whichever parameter in
Live that’s clicked on next.

The controls in the Output Range section depend on the Modulation toggle at the top right of the
device. This toggle sets how Expression Control’s modulation values are generated, and has two
modes: Modulate or Remote Control.

When Modulate is selected, base values of a mapped parameter can be adjusted using your cursor.
In this mode, the value set or automated by Expression Control will be merged with the value being set
as you tweak the parameter in question. When Remote Control is selected, modulated parameter
values are set by Expression Control and interaction with base parameter values is no longer possible.

The Modulation toggle also affects Expression Control’s polarity modes. When Modulate is selected,
a Modulation Polarity toggle in the Output Range section lets you choose between bipolar and
unipolar modes. In Bipolar mode, modulation is centered around the base parameter value being
modulated. In Unipolar mode, modulation is added to the base parameter value being modulated.
The Output Range Max slider sets the output modulation value generated when the input signal is at
its maximum amplitude. When Remote Control is selected, the Output Range section lets you set
minimum and maximum output modulation values using the Output Range Min and Output Range
Max sliders.

The Curve Type buttons below the Curve Display can be used to select a linear or S-shaped curve.
The type of curve selected determines which controls are available in the Curve section.

When a linear curve (with two breakpoints) is selected, the Curve A dial adjusts the modulation
curve’s entire shape. When an S-shaped curve (with three breakpoints) is selected, the Curve A dial
adjusts the curve’s upper segment shape and the Curve B dial adjusts its lower segment shape. When
the Curve Link button is enabled, the curve’s upper and lower segments can be inversely adjusted
using only the Curve A dial.

The Curve Display provides a visualization of the modulation curve being generated by the device.
Minimum and maximum values for the curve can be set via the Min/Max sliders. When an S-shaped
curve is selected, the middle breakpoint’s horizontal and vertical positions can be set via the X-Y
sliders. Breakpoints and curve shape can also be adjusted by clicking and dragging the visualized
curve directly in the display.

When Increment is selected as a modulation source in any MIDI Input Source drop-down menu, the
Increment Steps slider is activated. This value defines how many note triggers are necessary to cycle
through the device’s entire modulation range, and can be set to a value from 1 to 32 steps. Stopping

transport will reset the count, so that the first note played when transport restarts will output the
minimum modulation value that has been set.

When Random is selected as a modulation source in any MIDI Input Source drop-down menu, the
Random Amount slider is activated. This slider sets how much random deviation is applied to the target
modulation value with each note trigger.

The Smoothing Type toggle lets you choose between linear or logarithmic smoothing between
modulation values.

The Smoothing Rise and Fall sliders set the amount of time it takes for increasing and decreasing
modulation values to reach the most recent value, from 0 to 1000 milliseconds.

30.3.3 Expression Control Legacy

The Expression Control Legacy Effect.

Expression Control Legacy is a parameter modulation device that allows for a wide variety of internal
MIDI mappings. The MIDI controller’s Velocity, Modulation Wheel, Pitch Bend, Aftertouch and
Keytrack can each be mapped to one destination.

Activate a Map switch and click on a parameter in Live to assign that parameter as a mapping target.

You can set independent modulation intensities for each mapping via the Min and Max sliders.

The Log and Lin switches toggle between logarithmic and linear shapes.

The Rise slider smooths the attack of the envelope, while the Fall slider smooths the release of the
envelope.

The Output displays show the output level for each mapping.

30.3.4 MIDI Monitor

The MIDI Monitor Effect.

MIDI Monitor is a utility MIDI device that displays incoming MIDI and MPE data.

MIDI data can be viewed in either the Note display or Flow diagram.

In the Note display, incoming MIDI notes are shown along with their root note and related chords (if
played) on a keyboard layout. Note velocity is also shown.

The Flow diagram populates a list of incoming MIDI notes and data (such as pitch bend and
aftertouch messages) in a continuous stream as notes are played. The Freeze toggle can be used to
freeze or unfreeze the display, while the Clear button clears the entire display.

The Flow Diagram.

MPE data can be viewed in the MPE display. Incoming note, velocity, slide, pressure and per-note
pitch data are shown in a continuous stream as notes are played.

The MPE Display.

30.3.5 MPE Control

The MPE Control Effect.

MPE Control is a Max for Live MIDI effect that allows shaping and transforming incoming MPE (MIDI
Polyphonic Expression) signals, and offers distinctive adjustment options for each MPE data source. It
is typically used in conjunction with another device to fine-tune the effect MPE data has on mapped

parameters. MPE Control also allows converting MPE signals to global MIDI, making it possible to
use an MPE controller with non-MPE enabled instruments.

Before we get into the details of how you can use the MPE Control effect to shape the incoming MPE
data, let’s have a look at the difference between MPE and standard MIDI messages. MPE enables
MIDI Control Change (or MIDI CC) messages to be sent on a per-note basis, thus allowing you to
articulate each note individually. Without MPE, those messages are sent globally, meaning that all
notes are affected by the MIDI CC being used. For more detailed information on MPE check out the
Editing MPE chapter.

While MPE already allows a lot more musical expression than standard MIDI data, MPE Control
gives you the ability to shape the MPE signals to a greater extent using curves, making it possible to
play even more expressively. Let’s say you are using the Expression Control device and mapped its
Slide MIDI input to the Filter Freq knob in Operator. Any incoming MPE slide data will affect the filter
frequency. You can then use MPE Control to fine-tune the signal further, so that only very high slide
values will reach a high frequency cutoff.

In MPE Control, the incoming MPE signals can be transformed via two types of curves that can be
smoothed for consistent rise and fall times. There are three signal sources available: Press (pressure),
Slide, as well as NotePB (per-note pitch bend), and each can be adjusted individually.

The curve of the selected MPE source is shown in the foreground of the display, making that curve and
its respective controls available for editing. By default, all MPE sources are switched on, but they can
be deactivated separately by clicking on the toggles next to their names.

For each MPE source, you can choose between two types of curve settings in the bottom left corner of
the display: linear or S-shaped. The linear curve has two breakpoints, while the S-shaped curve has
three breakpoints.

Choosing the linear setting lets you adjust the curve in two ways. You can use either the Curve control
knob or click and drag the curve directly in the display. In addition to adjusting the curve, you can
also modify the minimum and maximum values using the Min and Max sliders, or by dragging the
breakpoints at the ends of the curve.

The linear setting provides one curve, creating a smooth ramp for the chosen modulation source,
either “compressing” the data, making it easier to stay in the lower range of values, or “expanding” it,
making it easier to reach higher values with less input.

When choosing the S-shaped curve, a third breakpoint is added to the middle of the curve’s line,
separating the curve into two distinct segments. This breakpoint is movable, allowing complete control
over the crossover point between the two segments, giving you the possibility to create much more
radical curves. The two segments are linked together by default. Toggling the Curve Link button
separates the segments from each other, so that they can be individually compressed or expanded
using the two independent Curve dials.

Note that the position of the breakpoint separating the two segments can be adjusted either by
directly clicking and dragging the breakpoint, or by using the X-Y controls at the bottom of the display.
The X-Y controls are only active when using the S-shaped curve.

Clicking on the triangular button in the bottom right of the visualization will unfold the advanced
settings panel.

MPE Control’s Expanded View.

All of the three modulation sources include the Smooth toggle which enables smoothing for the
currently selected source. Specific Rise and Fall values for each of the curves can be set
independently via the respective controls, and additional controls are available depending on the
source you are editing.

30.3.5.1 Press

The Press source can be used to alter MPE pressure data, which, similarly to polyphonic aftertouch, is
sent on a per-note basis when pressure is applied to a controller’s key or pad after it was initially
struck.

Press Advanced Settings.

Press includes a Default toggle, which gives you the option to set a default MPE value to use with
MIDI notes that do not contain MPE data. You can also choose to send the MPE pressure data to the
Slide instead of the Press source by using the Swap to Slide toggle. This is useful when, for example,
you want to adjust the modulation via the vertical axis, but are using a controller which only supports
polyphonic aftertouch.

The Press to AT setting converts the MPE pressure data to monophonic aftertouch, so that non-MPE
instruments can be modulated via an MPE controller.

30.3.5.2 Slide

The Slide source modifies MPE slide data (transmitted as MIDI CC 74), which corresponds to the
vertical position of the finger on the controller key or pad.

Slide Advanced Settings.

Slide also includes a Default toggle for use with non-MPE data, as well as a Centered switch which is
useful when playing pad-based MPE controllers. When Centered is switched on, MPE slide data is
transformed so that hitting the center of the pad generates a modulation value of zero, and the
modulation value increases progressively as the finger slides away from the center alongside the
vertical axis.

By default, Slide is set to Abs mode, which means that MPE slide values are interpreted as absolute.
Switching the mode to Rel (relative) will set the slide values to start in the middle of the range,
regardless of where the finger is on the key or pad. They can then only be modified by further
sweeping the finger up and down while holding a note. In the Ons (onset) mode, MPE slide values
will only be updated with a Note On. Note that onset mode will automatically deactivate smoothing.

The Slide to Mod option transforms MPE slide messages to Mod Wheel (CC1) messages, allowing to
modulate non-MPE enabled instruments with an MPE controller.

30.3.5.3 NotePB

The NotePB source modifies the MPE per-note pitch bend data, which is produced by horizontal
movement on the controller’s keys or pads. Pitch bend by definition only affects the pitch or pitches
being produced.

NotePB Advanced Settings.

In the NotePB advanced settings, you can adjust the Pitch Range, which is useful in cases where the
hardware controller and the instrument’s pitch bend range do not match. For example, a setting of 2x
allows mapping an MPE controller with a +/- 48 semitone pitch bend range to an instrument whose
pitch bend range is +/- 24 semitones. If the Note Pitch Bend MIDI CC is mapped to anything other
than pitch, using higher values helps to cover a larger modulation range with a smaller movement.

When the NotePB to PB switch is switched on, MPE per-note pitch bend messages are translated to
standard MIDI messages, which makes it possible for MPE-enabled MIDI controllers to still send MIDI
information to instruments that do not receive MPE messages.

30.3.6 Note Echo

The Note Echo Effect.

Note Echo is an echo delay effect that creates additional MIDI notes at specific time intervals with
decreasing velocity.

Activate the Sync switch, which allows using the Delay Time beat division chooser. The numbered
switches represent time delay in 16th notes. For example, selecting ”4” delays the signal by four 16th
notes, which equals one beat (a quarter note) of delay.

Changing the Delay Time field percentage value shortens and extends delay times by fractional
amounts, thus producing the ”swing” type of timing effect found in drum machines.

If the Sync switch is off, the delay time reverts to milliseconds. To edit the delay time, click and drag the
Delay Time slider up or down, or click in the field and type in a value.

The Input switches lets you toggle between Thru/Mute playback modes. When Thru is active, both the
MIDI note and echo are played back. When Mute is active, the MIDI note is muted and only the echo
is audible.

Pitch sets the transposition amount applied to the note with each repeat of the echo.

Delay sets the amount of velocity applied to the echo. The Fback parameter defines how much of the
channel’s output signal feeds back into the delay line’s input.

Switching on the MPE toggle allows incoming MPE data to be echoed alongside MIDI notes and
velocity data. Otherwise, MPE data is filtered out.

With the MPE toggle switched on, the Press, Slide, and Note PB sliders become active and define the
feedback amount for the pressure, slide and per-note pitch bend data respectively. Setting the
feedback amount to lower than 100% will cause the echoed MPE data to progressively decay with
each repetition.

30.3.7 Shaper MIDI

The Shaper MIDI Effect.

Like Shaper, Shaper MIDI uses multi-breakpoint envelopes to generate mappable modulation data.
Shaper MIDI can also be triggered dynamically using MIDI notes/velocity.

Activate the Map switch and click on a parameter in Live to assign that parameter as a mapping
target.

To assign an additional mapping target, click on the Multimap button at the top-right of the display.
You can select any of the unassigned Map switches and click on another parameter in Live to assign it
as a mapping target. A total of eight parameters can be assigned. To unassign a parameter, click on
the button to the right of its Map switch.

For each modulated parameter, the Min and Max sliders let you scale the resulting output range after
the modulation is applied.

You can create a breakpoint by clicking anywhere in the display. You can delete a breakpoint by
Shift -clicking on it. Hold down the Alt (Win) / Option (Mac) key while dragging to create
curved segments.

To clear the display, press the Clear button in the bottom left corner. To the right of the Clear button,
you can choose from one of six breakpoint presets and one random breakpoint generator.

You can adjust the size of the grid via the Grid slider. When Snap is enabled, all breakpoints that you
create or reposition will snap to grid lines.

The smaller display on the top right provides an oscilloscope-style view of the output signal. The Jitter
slider adds randomness to the waveform, while the Smooth control smooths value changes.

The Rate control specifies the envelope modulation speed. The switches to the right of the Rate control
toggle between frequency in Hertz and tempo-synced beat divisions.

Depth sets the overall intensity of the envelope modulation. The velocity sensitivity of the modulation
depth can be adjusted using the Velocity control.

The Offset control takes over the value of the mapped parameter so that the envelope can modulate
that value.

Echo adjusts the amount of the envelope echo, while the Time control sets the echo time in
milliseconds.

Activating the Loop switch will loop the modulation envelope as long as a MIDI note is held.

30.4 Max for Live MIDI Tools

In addition to Live’s MIDI Tools, you can also access Max for Live MIDI Tools to transform and
generate notes in clips. Max for Live MIDI Tools are AMXD files that can be used in the Transform or
Generative Tools tab/panel in the Clip View. You can edit or create Max for Live MIDI Tools in a Max
patcher like any other Max device.

There are two built-in Max for Live MIDI Tools included with Live Standard and Suite: Velocity Shaper
and Euclidean. If you use the Suite edition or the Standard edition with the Max for Live add-on, you
can also edit and build your own Max for Live MIDI Tools or use Max for Live MIDI Tools from third-
party creators.

In order for third-party Max for Live MIDI Tools to show up in the Transform and Generative tabs/
panels in the Clip View, save them in these folders on your computer:

•
•

Transformations: ~/Music/Ableton/User Library/MIDI Tools/Max Transformations
Generators: ~/Music/Ableton/User Library/MIDI Tools/Max Generators

Alternatively, you can save the third-party MIDI Tools’ AMXD files in any folder within Places in Live’s
browser.

31. MIDI and Key Remote Control

To liberate the musician from the mouse, most of Live’s controls can be remote-controlled with an
external MIDI controller and the computer keyboard. This chapter describes the details of mapping to
the following specific types of controls in Live’s user interface:

1.

2.

3.

4.
5.

Session View slots — Note that MIDI and computer key assignments are bound to the slots, not
to the clips they contain.
Switches and buttons — Among them the Track and Device Activator switches, the Control Bar’s
tap tempo, metronome and transport controls.
Radio buttons — A radio button selects from among a number of options. One instance of a
radio button is the crossfader assignment section in each track, which offers three options: The
track is assigned to the crossfader’s A position, the track is unaffected by the crossfader, or the
track is affected by the crossfader’s B position.
Continuous controls — Like the mixer’s volume, pan and sends.
The crossfader — The behavior of which is described in detail in the respective section of the
Mixing chapter.

31.1 MIDI Remote Control

Live can be controlled remotely by external MIDI control surfaces, such as MIDI keyboards or
controller boxes. Live also offers dedicated control via Ableton Push 1, Push 2, and Push 3.

Before we explain how remote control assignments are made and implemented, let’s first make the
distinction between MIDI remote control and a separate use of MIDI in Live: as the input for our MIDI
tracks. Let’s suppose that you are using a MIDI keyboard to play an instrument in one of Live’s MIDI
tracks. If you assign C-1 on your MIDI keyboard to a Session View Clip Launch button, that key will
cease playing C-1 of your MIDI track’s instrument, as it now ”belongs” solely to the Clip Launch
button.

MIDI keys that become part of remote control assignments can no longer be used as input for MIDI
tracks. This is a common cause of confusion that can be easily resolved by observing the Control Bar’s
MIDI indicators.

Before making any MIDI assignments, you will need to set up Live to recognize your control surfaces.
This is done in the Link, Tempo & MIDI tab of Live’s Settings, which can be opened with the Ctrl
,
(Win) / Cmd

, (Mac) keyboard shortcut.

31.1.1 Natively Supported Control Surfaces

Control Surfaces are defined via the menus in the Link, Tempo & MIDI tab. Up to six supported control
surfaces can be used simultaneously in Live.

Setting Up Control Surfaces.

Open the first chooser in the Control Surface column to see whether your control surface is supported
natively by Live; if it is listed here, you can select it by name, and then define its MIDI input and output
ports using the two columns to the right. If your controller is not listed here, don’t fret — it can still be
enabled manually in the next section, Manual Control Surface Setup.

Depending on the controller, Live may need to perform a ”preset dump” to complete the setup. If this
is the case, the Dump button to the right of your control surface’s choosers in the Live Settings will
become enabled. Before pressing it, verify that your control surface is ready to receive preset dumps.
The method for enabling this varies for each manufacturer and product, so consult your hardware’s
documentation if you are unsure. Finally, press the Dump button; Live will then set up your hardware
automatically.

31.1.1.1 Instant Mappings

In most cases, Live uses a standard method for mapping its functions and parameters to physical
controls. This varies, of course, depending upon the configuration of knobs, sliders and buttons on the
control surface. These feature-dependent configurations are known as instant mappings.

Within Live’s built-in lessons, you will find a Control Surface Reference that lists all currently supported
hardware, complete with the details of their instant mappings. Lessons can be accessed at any time by
selecting the Help View option from the View menu.

You can always manually override any instant mappings with your own assignments. In this case, you
will also want to enable the Remote switches for the MIDI ports that your control surface is using. This
is done in the MIDI Ports section of the Link, Tempo & MIDI Settings tab, and is described in the next
section.

Instant mappings are advantageous because the control surface’s controllers will automatically
reassign themselves in order to control the currently selected device in Live.

Control Surfaces Can Follow Device Selection.

In addition to following device selection, natively supported control surfaces can be ”locked” to
specific devices, guaranteeing hands-on access no matter where the current focus is in your Live Set.
To enable or disable locking, right-click on a device’s title bar, and then select your preferred
controller from the ”Lock to…” context menu. You’ll recognize the same list of control surfaces that you
defined in the Link, Tempo & MIDI Settings. By default, the instrument in a MIDI track will
automatically be locked to the control surface when the track is armed for recording.

Getting Hands-On: Control Surfaces Can Be Locked to Devices.

A hand icon in the title bar of locked devices serves as a handy reminder of their status.

Note: Some control surfaces do not support locking to devices. This capability is indicated for
individual controllers in the Control Surface Reference lesson. Select the Help View option from the
Help menu to access Live’s built-in lessons.

31.1.2 Manual Control Surface Setup

If your MIDI control surface is not listed in the Link, Tempo & MIDI Settings’ Control Surface chooser, it
can still be enabled for manual mapping in the MIDI Ports section of this tab.

Defining Control Surfaces Manually.

The MIDI Ports table lists all available MIDI input and output ports. To use an input port for remote
control of Live, make sure the corresponding switch in its Remote column is set to ”On.” You can use
any number of MIDI ports for remote mapping; Live will merge their incoming MIDI signals.

When working with a control surface that provides physical or visual feedback, you will also need to
enable the Remote switch for its output port. Live needs to be able to communicate with such control
surfaces when a value has changed so that they can update the positions of their motorized faders or
the status of their LEDs to match.

To test your setup, try sending some MIDI data to Live from your control surface. The Control Bar’s
MIDI indicators will flash whenever Live recognizes an incoming MIDI message.

Once your controller is recognized by Live, you have completed the setup phase (but we recommend
that you take the time to select a Takeover Mode before you leave the Settings behind). Your next step
will be creating MIDI mappings between your control surface and Live. Luckily, this is a simple task,
and you only need to do it for one parameter at a time.

31.1.3 Takeover Mode

MIDI Controller Takeover Mode.

When MIDI controls that send absolute values (such as faders) are used in a bank-switching setup,
where they address a different destination parameter with each controller bank, you will need to
decide how Live should handle the sudden jumps in values that will occur when moving a control for
the first time after switching the bank. Three takeover modes are available:

None — As soon as the physical control is moved, its new value is sent immediately to its destination
parameter, usually resulting in abrupt value changes.

Pick-Up — Moving the physical control has no effect until it reaches the value of its destination
parameter. As soon as they are equal, the destination value tracks the control’s value 1:1. This option
can provide smooth value changes, but it can be difficult to estimate exactly where the pick-up will
take place.

Value Scaling — This option ensures smooth value transitions. It compares the physical control’s value
to the destination parameter’s value and calculates a smooth convergence of the two as the control is
moved. As soon as they are equal, the destination value tracks the control’s value 1:1.

31.2 The Mapping Browser

The Mapping Browser.

All manual MIDI, computer keyboard and Macro Control mappings are managed by the Mapping
Browser. The Mapping Browser is hidden until one of the three mapping modes is enabled. It will then
display all mappings for the current mode. For each mapping, it lists the control element, the path to
the mapped parameter, the parameter’s name, and the mapping’s Min and Max value ranges. The
assigned Min and Max ranges can be edited at any time, and can be quickly inverted with a context
menu command. Delete mappings using your computer’s Backspace (Win) or Delete (Mac) key.

Note that Instant Mappings are context based and are not displayed in the Mapping Browser. Their
mapping structure can be displayed while working in Live by choosing the Help View option from the
Help menu and then opening the Control Surface Reference lesson.

31.2.1 Assigning MIDI Remote Control

The MIDI Map Mode Switch.

Once your remote control setup has been defined in the Link, Tempo & MIDI Settings, giving MIDI
controllers and notes remote control assignments is simple:

1.

Enter MIDI Map Mode by pressing the MIDI switch in Live’s upper right-hand corner. Notice
that assignable elements of the interface become highlighted in blue, and that the Mapping
Browser becomes available. If your browser is closed, Ctrl
Option

B (Win) / Cmd

B (Mac) will open it for you.

Alt

2.
3.

4.

Click on the Live parameter that you’d like to control via MIDI.
Send a MIDI message by pressing a keyboard key, turning a knob, etc., on your MIDI
controller. You will see that this new MIDI mapping is now listed in the Mapping Browser.
Exit MIDI Map Mode by pressing the MIDI switch once again. The Mapping Browser will
disappear, but you can always review your mappings by entering MIDI Map Mode again.

31.2.2 Mapping to MIDI Notes

MIDI notes send simple Note On and Note Off messages to Live’s interface elements. These messages
can produce the following effects on controls in Live:

•

•
•
•

Session View Slots — Note On and Note Off messages affect clips in the slot according to their
Launch Mode settings.
Switches — A Note On message toggles the switch’s state.
Radio Buttons — Note On messages toggle through the available options.
Variable Parameters — When assigned to a single note, Note On messages toggle the
parameter between its Min and Max values. When assigned to a range of notes, each note is
assigned a discrete value, equally spaced over the parameter’s range of values.

Session View slots can be assigned to a MIDI note range for chromatic playing: First play the root key
(this is the key that will play the clip at its default transposition), and then, while holding down the root
key, hold one key below the root and one above it to define the limits of the range.

31.2.3 Mapping to Absolute MIDI Controllers

Absolute MIDI controllers send messages to Live in the form of absolute values ranging from 0 to 127.
These values lead to different results depending on the type of Live control to which they are assigned.
A value message of 127, for example, might turn the Volume control on a Live track all the way up or

play a Session View clip. Specifically, MIDI controller messages from 0 to 127 can produce the
following effects on controls in Live:

•

•

•

•

Session View Slots — Controller values 64 and above are treated like Note On messages.
Controller values 63 and below are treated like Note Off messages.
Switches — For track activators and on/off buttons in devices, controller values that are within
the mapping’s Min and Max range turn the switch on. Controller values that are above or
below this range turn it off. You can reverse this behavior by setting a Min value that is higher
than its corresponding Max value. In this case, controller values that are outside of the range
turn the switch on, while values inside the range turn it off. For all other switches (such as
transport controls), controller values 64 and above turn the switch on, while controller values
below 64 turn it off.
Radio Buttons — The controller’s 0…127 value range is mapped onto the range of available
options.
Continuous Controls — The controller’s 0…127 value range is mapped onto the parameter’s
range of values.

Live also supports pitch bend messages and high-precision (”14-bit Absolute”) controller messages
with a 0…16383 value range. The above specifications apply to these as well, except that the value
range’s center is at 8191/8192.

31.2.4 Mapping to Relative MIDI Controllers

Some MIDI controllers can send ”value increment” and ”value decrement” messages instead of
absolute values. These controls prevent parameter jumps when the state of a control in Live and the
corresponding control on the hardware MIDI controller differ. For example, imagine that you have
assigned the pan knob on your control surface to the pan parameter of a track in Live. If the hardware
control is panned hard right, and the Live control is panned hard left, a slight movement in a hardware
pan knob that sends absolute values would tell Live to pan right, causing an abrupt jump in the track’s
panning. A pan knob sending relative messages would prevent this, since its incremental message to
Live would simply say, ”Pan slightly to the left of your current position.”

There are four types of relative controllers: Signed Bit, Signed Bit 2, Bin Offset and Twos Complement.

Each of these are also available in a ”linear” mode. Some MIDI encoders use ”acceleration”
internally, generating larger changes in value when they are turned quickly. For control surfaces that
are not natively supported, Live tries to detect the controller type and whether acceleration is being
used or not.

You can improve the detection process by moving the relative controller slowly to the left when you
make an assignment. Live will offer its suggestion in the Status Bar’s ”mode” chooser, but if you
happen to know the relative controller type, you can manually select it.

Live will do the following with relative MIDI controller messages:

•

Session View Slots — Value increment messages are treated like Note On messages. Value
decrement messages are treated like Note Off messages.

•
•

•

Switches — Increment messages turn the switch on. Decrement messages turn it off.
Radio Buttons — Increment messages make the radio button jump forward to the next available
option. Decrement messages make it jump backward.
Continuous Controls — Each type of relative MIDI controller uses a different interpretation of
the 0…127 MIDI controller value range to identify value increments and decrements.

Please consult the documentation that came with your MIDI controller if you need further information
on relative MIDI controllers.

31.2.4.1 Relative Session View Navigation

Notice that you can make not only absolute mappings to individual slots and scenes, but also relative
mappings to move the highlighted scene and operate on the highlighted clips.

In both MIDI Map Mode and Key Map Mode, a strip of assignable controls appears below the
Session grid:

The Relative Session Mapping Strip.

1.
2.

3.

4.
5.

Assign these buttons to keys, notes or controllers to move the highlighted scene up and down.
Assign this scene number value box to a MIDI controller — preferably an endless encoder — to
scroll through the scenes. For details, see the previous section on Relative Map Modes.
Assign this button to launch the highlighted scene. If the Record, Warp & Launch Settings’ Select
Next Scene on Launch option is checked, you can move successively (and hopefully
successfully!) through the scenes.
Assign this button to cancel the launch of a triggered scene.
Assign these buttons to launch the clip at the highlighted scene, in the respective track.

Relative Session mapping is useful for navigating a large Live Set, as Live always keeps the
highlighted scene at the Session View’s center.

31.2.4.2 Mapping to Clip View Controls

The Clip View displays the settings for whichever clip happens to be currently selected, but it will also
display the settings of multi-selected clips. To avoid unpleasant musical surprises, it is important to
remember that creating remote control mappings for any control in the Clip View interface could

potentially affect any clip in the Live Set. For this reason, we recommend mapping Clip View controls
to relative MIDI controllers to prevent undesirable jumps in parameter values.

31.2.5 Computer Keyboard Remote Control

The Key Map Mode Switch.

Creating control surface assignments for your computer keyboard is straightforward:

1.

2.

3.

4.

Enter Key Map Mode by pressing the KEY switch in the upper right-hand corner of the Live
screen. Notice that the assignable elements of the interface become highlighted in red when
you enter Key Map Mode. The Mapping Browser will also become available. If the Browser is
hidden, you will want to show it at this point using the appropriate View menu command.
Click on the Live parameter that you wish to assign to a key. Remember that only the controls
that are shown with a red overlay are available for mapping.
Press the computer key to which you wish to assign the control. The details of your new
mapping will be displayed in the Mapping Browser.
Leave Key Map Mode by pressing Live’s KEY switch once again. The Mapping Browser will
disappear, but your mappings can be reviewed at any time simply by entering Key Map Mode
again.

Keyboard assignments can produce the following effects in Live:

•

•
•

Clips in Session View slots will be affected by mapped keys according to their Launch Mode
settings.
Keys assigned to switches will toggle switch states.
Keys assigned to radio buttons will toggle through the available options.

Please be sure not to confuse this remote control functionality with Live’s ability to use the computer
keyboard as a pseudo-MIDI keyboard that can generate MIDI notes from computer keystrokes for
use with instruments.

32. Using Push 1

Ableton Push 1 is an instrument for song creation that provides hands-on control of melody and
harmony, beats, sounds, and song structure. In the studio, Push 1 allows you to quickly create clips
that populate Live’s Session View as you work entirely from the hardware. On stage, Push 1 serves as
a powerful instrument for clip launching.

Push 1’s controls are divided into a number of sections, as shown in the diagram below.

Overview of Push 1’s Controls.

Much of Push 1’s behavior depends on which mode it is in, as well as on which type of track is
selected. To help you learn how to work with Push 1, this chapter will walk you through some of the
fundamental workflows, and then will provide a reference of all of Push 1’s controls.

There are also a number of videos that will help you get started with Push 1. These are available at
https://www.ableton.com/learn-push/

32.1 Setup

Setting up the Push 1 hardware is mostly automatic. As long as Live is running, Push 1 will be
automatically detected as soon as it is connected to a USB port on your computer. After connection,
Push 1 can be used immediately. It is not necessary to install drivers and Push 1 does not need to be
manually configured in Live’s Settings.

32.2 Browsing and Loading Sounds

You can browse and load sounds directly from Push 1, without needing to use Live’s browser. This is
done in Push 1’s Browse Mode.

Press Push 1’s Browse button:

The Browse Button.

In Browse Mode, the display shows all of your available sounds and effects, as well as locations from
the Places section of Live’s browser. The display is divided into columns. The far left column shows
either the specific type of device being browsed or the Places label. Each column to the right shows
the next subfolder (if any exist). Use the In and Out buttons to shift the display to the right or left,
allowing you to browse deeper levels of subfolders or view a larger number of presets on the display.

In and Out Buttons.

Navigate up via the Selection Control button (the first row below the display) in each column.
Navigate down one folder via the State Control button for each level (the second row below the
display). Samples and presets from official Packs or Live’s Core Library will preview when selected in
the browser. To load a device preset, press the green button on the right. To load the default preset of
the selected device, press the green button on the left.

Loading Devices or Device Presets in Browse Mode.

You can scroll quickly through folders and subfolders via the encoders. Holding Shift while pressing
the up or down buttons will move by a whole page.

After pressing a device or preset load button, the button will turn amber. This indicates that the
currently selected entry is loaded; if you navigate to a different entry, the button will turn green again.
Pressing an amber load button will load the next entry in the list, allowing you to quickly try out
presets or devices.

What you see when in Browse Mode depends on the device that was last selected. If you were
working with an instrument, Browse Mode will show you replacement instruments. If you were
working with an effect, you will see effects. When starting with an empty MIDI track, the display
shows all of your available sounds, instruments, drum kits, effects, and Max for Live device, as well as
VST and Audio Units plug-ins. Folders are only visible on Push 1 if they contain items that can be
loaded at any particular time. For example, the Samples label (as well as any of your own folders in
Places that only contain samples) won’t be visible unless you’re browsing from a single pad in a Drum
Rack.

32.3 Playing and Programming Beats

To create beats using Push 1, first make sure Note Mode is enabled.

The Note Mode Button.

Then use Browse Mode to load one of the Drum Rack presets from Live’s library.

When working with a MIDI track containing a Drum Rack, Push 1’s 8x8 pad grid can be configured in
a few different ways, depending on the state of the Note button. Pressing this button cycles between
three different modes.

32.3.1 Loop Selector

When the Loop Selector layout is enabled, the pads are divided into three sections, allowing you to
simultaneously play, step sequence and adjust the length of your clip.

The Pad Grid When Working With Drums

The 16 Drum Rack pads are laid out, like Live’s Drum Rack, in the classic 4x4 arrangement, allowing
for real-time playing. The Drum Rack pad colors indicate the following:

•
•
•
•
•
•

Bright yellow — this pad contains a sound.
Dull yellow — this pad is empty.
Green — this pad is currently-playing.
Light Blue — this pad is selected.
Dark blue — this pad is soloed.
Orange— this pad is muted.

When working with Drum Racks that contain a larger number of pads, use Push 1’s touch strip or the
Octave Up and Octave Down keys to move up/down by 16 pads. Hold Shift while using the touch
strip or Octave keys to move by single rows.

Holding the Note button gives you momentary access to the 16 Velocities layout. You can also lock
the alternate layout in place by holding Shift and pressing the Note button. To unlock the 16 Velocities
layout, press the Note button again.

Octave Up/Down Buttons.

32.3.2 16 Velocities Mode

Press the Layout button to switch to the 16 Velocities layout. In this mode, the bottom right 16 pads
represent 16 different velocities for the selected Drum Rack pad. Tap one of the velocity pads to enter
steps at that velocity.

Holding the Note button gives you momentary access to the loop length controls. You can also lock
the loop length controls in place by holding Shift and pressing the Note button. To unlock the loop
length pads, press the Note button again.

32.3.3 64-Pad Mode

In addition to the Loop Selector and 16 Velocities layouts, you can also use the entire 8x8 pad grid
for real-time drum playing. This is useful when working with very large drum kits, such as those created
by slicing. To toggle to 64-pad mode, press the Note Mode button a second time. Pressing Note
again will then toggle back to the Loop Selector layout, allowing you to quickly get back to step
sequencing. The pad colors in 64-pad mode are the same as those used in the three-section layout.

When moving back and forth between the three layouts, the 16 pads available for step sequencing
will not change automatically. You may still need to use the touch strip or Octave keys in order to see
the specific 16 pads you want.

Holding the Note button gives you momentary access to the loop length controls. You can also lock
the loop length controls in place by holding Shift and pressing the Note button. To unlock the loop
length pads, press the Note button again.

32.3.4 Loading Individual Drums

Browse Mode can also be used to load or replace individual pads within a loaded Drum Rack. To
switch between browsing Drum Racks and single pads, press the Device button to show the devices
on the track.

Device Button.

By default, the Drum Rack is selected, as indicated by the arrow in the display. To select an individual
pad instead, tap that pad, then press the selection button below the pad’s name.

Selecting an Individual Pad in a Drum Rack.

Now, entering Browse Mode again will allow you to load or replace the sound of only the selected
pad. Once in Browse Mode, tapping other pads will select them for browsing, allowing you to quickly
load or replace multiple sounds within the loaded Drum Rack.

32.3.4.1 Additional Pad Options for Push 1

To copy a pad to a different location in your Drum Rack, hold the Duplicate button and press the pad
you’d like to copy. While continuing to hold Duplicate, press the pad where you’d like to paste the
copied pad. Note that this will replace the destination pad’s devices (and thus its sound) but will not
replace any existing notes already recorded for that pad.

32.3.5 Step Sequencing Beats

Tapping a pad also enables it for step sequencing. To select a pad without playing it, press and hold
the Select button while tapping a pad.

Select Button.

To record notes with the step sequencer, tap the pads in the step sequencer controls to place notes in
the clip where you want them. The clip will begin playing as soon as you tap a step. By default, each
step sequencer pad corresponds to a 16th note, but you can change the step size via the buttons in
the Scene/Grid section.

Scene/Grid Buttons.

As the clip plays, the currently playing step is indicated by the moving green pad in the step
sequencer section. When Record is enabled, the moving pad will be red. Tapping a step that already
has a note will delete that note. Press and hold the Mute button while tapping a step to deactivate it
without deleting it. Press and hold Solo button while tapping a pad to solo that sound.

Mute and Solo Buttons.

You can also adjust the velocity and micro-timing of individual notes, as described in the section on
step sequencing automation.

To delete all notes for a pad, press and hold Delete while tapping the pad. Note that this will only
delete notes that are within the current loop.

Delete Button.

The pad colors in the step sequencer section indicate the following:

•
•
•
•

Unlit — this step doesn’t contain a note.
Blue — this step contains a note. Darker blues indicate higher velocities.
Dull yellow — this step contains a note, but the note is muted.
Light Red — the right two columns of pads will turn red if triplets are selected as the step size. In
this case, these pads are not active; only the first six pads in each row of steps can be used.

When Triplets are Selected, the Red Steps are Unavailable.

For detailed information about adjusting the loop length pads, see the section called Adjusting the
Loop Length.

32.3.6 Real-time Recording

Drum patterns can also be recorded in real-time by playing the Drum Rack pads. Follow these steps to
record in real-time:

•

If you want to record with a click track, press the Metronome button to enable Live’s built-in
click

Metronome Button.

•

Then Press the Record button to begin recording

Record Button.

Now any Drum Rack pads you play will be recorded to the clip. Pressing Record again will stop
recording but will continue playing back the clip. Pressing Record a third time will enable overdub
mode, allowing you to record into the clip while it plays back. Subsequent presses continue to toggle
between playback and overdub.

Pressing New stops playback of the currently selected clip and prepares Live to record a new clip on
the currently selected track. This allows you to practice before recording a new idea. By default,
pressing New also duplicates all clips that are playing on other tracks to a new scene and continues
playing them back seamlessly. This behavior can be changed by changing the Workflow mode in
Push 1’s User Preferences.

New Button.

32.3.7 Fixed Length Recording

Press the Fixed Length button to set the size of new clips to a predetermined length.

Fixed Length Button.

Press and hold Fixed Length to set the recording length.

Fixed Length Recording Options.

When Fixed Length is disabled, new clips will continue to record until you press the Record, New or
Play/Stop buttons.

Enabling Fixed Length while recording will switch recording off and loop the last few bars of the clip,
depending on the Fixed Length setting.

32.4 Additional Recording Options

32.4.1 Recording with Repeat

With Push 1’s Repeat button enabled, you can hold down a pad to play or record a stream of
continuous, rhythmically-even notes. This is useful for recording steady hi-hat patterns, for example.
Varying your finger pressure on the pad will change the volume of the repeated notes.

Repeat Button.

The repeat rate is set with the Scene/Grid buttons. Note that Push 1 “remembers” the Repeat button’s
state and setting for each track.

If you press and release Repeat quickly, the button will stay on. If you press and hold, the button will
turn off when released, allowing for momentary control of repeated notes.

Turn up the Swing knob to apply swing to the repeated notes. When you touch the knob, the display
will show the amount of swing.

Swing Knob.

32.4.2 Quantizing

Pressing Push 1’s Quantize button will snap notes to the grid in the selected clip.

Quantize Button.

Press and hold Quantize to change the quantization options:

Quantization Options.

Swing Amount determines the amount of swing that will be applied to the quantized notes. Note that
the Swing amount can be adjusted from Encoder 1 or from the dedicated Swing knob.

Quantize To sets the nearest note value to which notes will be quantized, while Quantize Amount
determines the amount that notes can be moved from their original positions.

Enable Record Quantize to automatically quantize notes while recording and adjust the record
quantization value with Encoder 8. Note that these controls correspond to the settings of the Record
Quantization chooser in Live’s Edit menu, and adjustments can be made from Live or from Push 1.

When working with drums, press and hold Quantize and press a Drum Rack pad to quantize only that
drum’s notes in the current clip.

32.5 Playing Melodies and Harmonies

After working on a beat, you’ll want to create a new track so that you can work on a bassline,
harmony parts, etc. Press the Add Track button to add a new MIDI track to your Live Set.

Add Track Button.

Press and hold the Add Track button to select between Audio, MIDI and Return tracks.

Adding a track puts Push 1 into Browse mode, so you can immediately load an instrument. After
loading your instrument, make sure Note Mode is enabled.

Note that when pressing the Add Track button while a track within a Group Track is selected, any new
tracks will be inserted into that Group Track.

When working with a MIDI track containing an instrument, Push 1’s 8x8 pad grid automatically
configures itself to play notes. By default, every note on the grid is in the key of C major. The bottom
left pad plays C1 (although you can change the octave with the Octave Up and Down buttons).
Moving upward, each pad is a fourth higher. Moving to the right, each pad is the next note in the C
major scale.

Play a major scale by playing the first three pads in the first row, then the first three pads in the next
row upwards. Continue until you reach the next C:

C Major Scale.

The pad colors help you to stay oriented as you play:

•
•
•
•

Blue — this note is the root note of the key (e.g., C).
White — this note is in the scale, but is not the root.
Green — the currently-playing note (other pads will also turn green if they play the same note).
Red — the currently-playing note when recording.

To play triads, try out the following shape anywhere on the grid:

C Major Chord.

Holding the Note button gives you momentary access to the loop length controls, which appear in the
top row of pads. You can lock the loop length controls in place by holding Shift and pressing the Note
button. To unlock the loop length pads, press the Note button again.

32.5.1 Playing in Other Keys

Press Push 1’s Scales button to change the selected key and/or scale.

Scales Button.

Using the display and the Selection and State Control buttons, you can change the key played by the
pad grid. The currently selected key is marked with an arrow in the display:

By default, the pads and scale selection options indicate major scales. You can change to a variety of
other scale types using the first encoder, or the two buttons below the display on the far left. The
selected scale type is also marked with an arrow.

Key and Scale Selection.

In addition to changing the key, you can also change the layout of the grid using the two buttons on
the far right.

Fixed Y/N: When Fixed Mode is on, the notes on the pad grid remain in the same positions when you
change keys; the bottom-left pad will always play C, except in keys that don’t contain a C, in which
case the bottom-left pad will play the nearest note in the key. When Fixed is off, the notes on the pad
grid shift so that the bottom-left pad always plays the root of the selected key.

In Key/Chromatic: With In Key selected, the pad grid is effectively “folded” so that only notes within
the key are available. In Chromatic Mode, the pad grid contains all notes. Notes that are in the key
are lit, while notes that are not in the key are unlit.

Holding the Shift button while in Scales mode allows you to access a number of additional note
layout options.

Additional Note Layout Options.

The “4th” and “3rd “options refer to the note interval that the grid is based on, while the ^ and >
symbols refer to the rotation of the grid. For example, the default layout is “4th ^” which means that
each row of pads is a 4th higher than the row below it. The “4th >” option is also built on 4ths, but
now moves to the right rather than upwards; each column is a 4th higher than the column to the left.
The “Sequent” options lay out all notes in order. These options are useful if you need a very large
range of notes available, because they have no duplicated notes.

The last settings that you chose in the Scale options (key, scale type, In Key/Chromatic, and Fixed Y/
N) are saved with the Set. Push 1 will return to these settings when the Set is reloaded again.

All of the real-time recording options available for drums are also available for melodies and
harmonies, including fixed length recording, recording with repeat, and quantizing. But for detailed
editing, you’ll work with the melodic step sequencer described in the next section.

One editing possibility is available in the real-time Note Mode: to quickly delete all notes of the same
pitch within the current loop, press and hold Delete and then tap the respective pad.

32.6 Step Sequencing Melodies and Harmonies

In addition to playing and recording in real time, you can also step sequence your melodies and
harmonies. To toggle to the Melodic Sequencer, press the Note Mode button a second time. This will
set the 8x8 pad grid as follows:

The Pad Grid When Step Sequencing Pitches.

When using the Melodic Sequencer, all eight rows of pads allow you to place notes in the clip. You
can adjust the loop length and access additional step sequencing pages via the loop length pads. The
loop length pads can be momentarily accessed in the top row while holding the Note button.

You can also lock the loop length pads in place. To do this, hold Shift and tap the Note button. Note
that Push 1 remembers this locked/unlocked state for each track. To unlock the loop length pads,
press the Note button again.

With In Key selected, each row corresponds to one of the available pitches in the currently selected
scale. With Chromatic selected, notes that are in the key are lit, while notes that are not in the key are
unlit. The light blue row (which is the bottom row by default) indicates the root of the selected key.
Each column of pads represents a step in the resolution set by the Scene/Grid buttons.

As with the real-time playing layout, pressing the Octave Up and Down button shifts the range of
available notes. You can also use the touch strip to change the range. Hold the Shift key while
adjusting the touch strip or pressing the Octave buttons to fine tune the pitch range. After adjusting the
pitch range or when switching between the real-time and step sequencing layouts, the display will
briefly show the available range.

The Display Shows the Range of Available Notes.

Additionally, brightly-lit touch strip lights indicate the currently available note range, while dimly-lit
touch strip lights indicate that the clip contains notes within the corresponding note range.

Pressing Note again will toggle to the Melodic Sequencer + 32 Notes layout.

In addition to adding and removing notes, you can also adjust the velocity and micro-timing of the
notes, as described in the section on step sequencing automation.

32.6.1 Adjusting the Loop Length

The loop length controls allow you to set the length of the clip’s loop and determine which part of it
you can see and edit in the melodic and drum step sequencers. Each loop length pad corresponds to
a page of steps, and the length of a page depends on the step resolution. When working with drums
at the default 16th note resolution, two pages of steps are available at a time, for a total of two bars.
In the Melodic Sequencer layout, one page of eight steps is available at a time, for a total of two
beats. To change the loop length, hold one pad and then tap another pad or, to set the loop length to
exactly one page, quickly double-tap the corresponding pad.

Each Loop Length Pad Corresponds to One Page.

Note that the page you see is not necessarily the page you hear. When you set the loop length, the
pages will update so that the current play position (as indicated by the moving green pad in the step
sequencer section) always remains visible. But in some cases, you may want to disable this auto-
follow behavior. For example, you may want to edit a single page of a longer loop, while still
allowing the loop to play for the length you set. To do this, single-tap the pad that corresponds to that
page. This will “lock” the view to that page without changing the loop length. To then turn auto-follow
back on, simply reselect the current loop. Note that single-tapping a page that is outside of the current
loop will immediately set the loop to that page.

The pad colors in the loop length section indicate the following:

•
•
•
•

Unlit — this page is outside of the loop.
White — this page is within the loop, but is not currently visible in the step sequencer section.
Dull yellow — this page is visible in the step sequencer section, but is not currently playing.
Green — this is the currently playing page.

If you need to access the loop length pads frequently, you can lock them in place. To do this, hold
Shift and tap the Note button. Note that Push 1 remembers this locked/unlocked state for each track.
To unlock the loop length pads, press the Note button again.

To duplicate the contents of a sequencer page, hold Duplicate, press the loop length pad for the page
you want to duplicate, and press the loop length pad for the destination page. Note that this will not
remove existing notes in the destination page, but will add copied notes on top. To remove notes first,
hold Delete and tap the loop length pad for that page.

32.7 Melodic Sequencer + 32 Notes

The Melodic Sequencer + 32 Notes layout combines both step sequencing and real-time playing
capabilities. Providing access to multiple octaves and steps on a single page, this layout is ideal for
figuring out chords and harmonies to sequence. It is also well suited to longer phrases.

32.7.1 32 Notes

The bottom half of the pad grid lets you play notes in real-time, and select them for step sequencing.
Each pad corresponds to one of the available pitches in the currently selected scale. Pressing a pad
will select and play the note. Selected notes are represented by a lighter version of the track’s color.

To select a pad without triggering it, press and hold the Select button while tapping a pad.

The pad colors indicate the following:

•
•
•
•

Blue — this note is the root note of the scale.
Blue-Green — this pad is selected.
Green — this pad is currently playing.
White — this note is in the scale, but is not the root.

Pressing the Octave Up or Down button shifts the range of available notes. Holding the Shift key while
adjusting the touch strip shifts the range by octaves. You can hold the Shift key while pressing the
Octave buttons to shift by one note in the scale. The display will briefly show the available range as
you adjust it.

As with the 64 Notes layout, the notes in the bottom half of the pad grid can be adjusted via the Scale
menu.

32.7.2 Sequencer

Tapping a step in the top half of the pad grid adds all selected notes to that step. Steps containing
notes are displayed in a blue color.

Holding a step lets you view notes contained within the step, which are indicated in the bottom half of
the pad grid by a blue-green color. Tapping any of these selected notes will remove it from the step.

Holding multiple steps will add selected notes to all those steps. While holding Duplicate, you can
press a step to copy the notes in that step and then press another step to paste them to a new location
in the step sequencer. Note that this will not remove existing notes in the destination page, but will add
copied notes on top. To remove notes first, hold Delete and tap the loop length pad for that page.

The pad colors in the step sequencer indicate the following:

•
•
•
•
•
•

Blue — this step contains a note.
Green — this step is currently playing.
White — this step is selected.
Dull Yellow — this step contains a note, but the note is muted.
Gray — this pad is empty.
Light Red — the right two columns of pads will be unlit if triplets are selected as the step size. In
this case, these pads are not active; only the first six pads in each row of steps can be used.

When working with the sequencer at the default 16th note resolution, two pages of steps are
available at a time, for a total of two bars. You can adjust the loop length and access additional step
sequencing pages via the loop length pads. The loop length pads can be momentarily accessed in the
fifth row while holding the Note button.

You can also lock the loop length pads in place. To do this, hold Shift and tap the Note button. Note
that Push 1 remembers this locked/unlocked state for each track. To unlock the loop length pads,
press the Note button again.

To duplicate the contents of a sequencer page, hold Duplicate, press the loop length pad for the page
you want to duplicate, and press the loop length pad for the destination page. Note that this will not
remove existing notes in the destination page, but will add copied notes on top. To remove notes first,
hold Delete and tap the loop length pad for that page.

32.8 Navigating in Note Mode

Now that you’ve created a few tracks, you can continue to add more. But you may want to move
between already-existing tracks to continue working on musical ideas using those instruments and
devices. The Arrow Keys allow you to do this.

Arrow Keys.

The Left/Right Arrows move between tracks. Note that selecting a MIDI track on Push 1 automatically
arms it, so it can be played immediately. In Live, track Arm buttons will appear pink to indicate that
they have been armed via selection.

Pink Track Arm Button.

The specific behavior of the Up/Down Arrows is determined by the Workflow mode, which is set in
Push 1’s User Preferences. In both modes, the Up/Down Arrows move up or down by a single scene.
In Scene Workflow, the selected scene is triggered. In Clip Workflow, only the selected track’s clip is
triggered. Clips in other tracks are not affected.

Navigating with the Up/Down Arrows in Note Mode always begins playback immediately, and a
triggered clip will take over the play position from whatever clip was played in that track before. Note
that this is the same behavior as if the clips were set to Legato Mode in Live.

32.9 Controlling Live’s Instruments and Effects

Pressing the Device button puts Push 1 in Device Mode, which allows Push 1’s encoders to control
parameters in Live’s devices.

Device Button.

In Device Mode, the Selection Control buttons select devices in the currently selected track, while the
State Control buttons turn the selected device on or off. The currently selected device is marked with
an arrow in the display.

Device Mode Settings.

The In and Out buttons allow you to navigate to additional devices and parameters that may not be
immediately available.

In and Out Buttons.

Use these buttons to access:

•
•

Additional banks of parameters (for effects that have more than one bank of parameters).
Additional device chains within Racks that contain more than one chain.

32.10 Mixing with Push 1

To control volumes, pans, or sends with the encoders for up to eight tracks simultaneously, press the
corresponding button on Push 1. Hold Shift while adjusting the encoders for fine-tune control.

Volume and Pan & Send Buttons.

In Volume Mode, the encoders control track volume.

Pressing the Pan & Send button repeatedly will cycle between controlling pans and however many
sends are available in your Live Set.

Press Push 1’s Track button to enable Track Mode.

Track Button.

In Track Mode, the encoders control track volume, pan and the first six sends of the selected track.
Press the Selection Control buttons to select which track will be controlled in Track Mode.

Selecting Tracks in Track Mode.

Press the Master button to select the Main track.

Press and hold a Group Track’s Selection Control button to unfold or fold the track.

Note that when Split Stereo Pan Mode is active while in Pan & Send Mode, the display will show the
current pan value, but the pan dial will be disabled. In Track Mode, the display will show either the
pan control or stereo pan sliders, depending on the active pan mode.

32.11 Recording Automation

Changes that you make to device and mixer parameters can be recorded to your clips as automation,
so that the sound will change over time as the clip plays. To record automation, press Push 1’s
Automation button.

Automation Button.

This toggles Live’s Session Automation Arm button, allowing you to record changes you make to Push
1’s encoders as part of the clip. When you’re done recording parameter changes, press the
Automation button again to turn it off. To delete the changes you’ve recorded for a particular
parameter, press and hold the Delete button and touch the corresponding encoder. If automation
hasn’t been recorded for a parameter, holding Delete and touching an encoder will reset the
corresponding parameter to its default value.

Automated parameters are shown with a rectangle next to the parameter name in the display.
Parameters that you have overridden (by manually adjusting the parameter while not recording) will
show their value in brackets.

Automated and/or Overridden Parameters are Indicated in the Display.

To reenable all automation that you have manually overridden press and hold Shift and press the
Automation button.

32.12 Step Sequencing Automation

In both the drum and melodic step sequencers, it’s possible to automate parameters for the selected
step.

The parameters that are available will change depending on the display mode you are currently in, as
explained in the following sections.

32.12.1 Note-Specific Parameters

When working in any sequencing layout in Clip Mode, you can adjust note settings for each step. To
access these settings, simply press and hold a step. The display will switch the controls to the step’s
note settings.

Hold a Step to Adjust Note and Automation Parameters.

You can then adjust the corresponding encoders in order to:

•

•
•
•

Nudge notes backwards or forwards in time. The value represents the percentage that the note
is offset from the previous grid line. Negative values indicate that the note occurs before the
grid line.
Adjust the coarse Length of the selected notes.
Fine-tune the length adjustment of the selected notes
Change the Velocity of the selected notes.

You can also adjust these note-specific parameters for multiple steps at the same time. To do this, press
and hold all of the pads you’d like to adjust, and then tweak the encoders. The display will show the
range of values for the selected steps.

With Multiple Steps Selected, the Display Shows the Range of Parameter Values.

You can also create notes with your desired Nudge, Length, and Velocity values by holding an empty
step and then tweaking any of these encoders.

When working with drums, you can adjust nudge, length, and velocity for every note played by a
particular pad by pressing and holding the Select button, pressing the pad, and then adjusting the
encoders.

Hold Select and Press a Drum Pad to Tweak All Notes Played by that Pad.

In both the drum and melodic step sequencers, you can copy a step (including all of its note-specific
parameters) and paste it to another step. To do this, hold Duplicate and tap the step you’d like to
copy. Then tap the destination step and release Duplicate.

32.12.2 Per-Step Automation

When in Device Mode or Volume Mode, hold one or more steps in order to create and edit device or
mixer automation for only the selected step(s). While holding a step and tweaking an encoder, the
corresponding parameter’s automation value will be adjusted specifically for the time represented by
that step. Note that per-step automation can be created for any step, even if that step doesn’t contain
notes.

32.13 Controlling Live’s Session View

Press Push 1’s Session button to switch from Note Mode to Session Mode. You can press and hold the
Session button to temporarily toggle Session Mode. Releasing the button will then return to Note
Mode. Likewise, pressing and holding Note while in Session Mode will temporarily toggle Note
Mode.

Session Button.

In Session Mode, the 8x8 pad grid will now launch clips and the Scene/Grid Buttons will launch
scenes. Pressing a pad triggers the clip in the corresponding location in Live’s Session View. If the track
is selected, pressing the button records a new clip.

The pads light up in different colors so you know what’s going on:

•
•
•

The color of all non-playing clips in your Live Set is reflected on the pads.
Playing clips pulse green to white.
Recording clips pulse red to white.

You can stop all music in a track by enabling Stop Mode and pressing that track’s State Control
button.

Stopping Clip Playback.

To stop all clips, press and hold Shift, and then press Stop.

Push 1 tells you what’s going on in the software, but, importantly, the software also reflects what’s
happening on the hardware. The clip slots currently being controlled by Push 1’s pad grid are shown
in Live with a colored border.

The directional arrows and Shift button increase the scope of the eight-by-eight grid.

•

•

Pressing Up or Down moves you up or down one scene at a time. Hold the Shift button while
hitting Up or Down to move eight scenes up or down. You can also use the Octave Up and
Down buttons to move by eight scenes at a time.
The Left and Right arrow keys move you left or right one track at a time. Hold the Shift button
while hitting Left or Right to move eight tracks at a time.

32.13.1 Session Overview

Push 1’s Session Overview lets you navigate through large Live Sets quickly without looking at your
computer screen. Hold down the Shift button and the pad grid zooms out to reveal an overview of
your Session View. In the Session Overview, each pad represents an eight-scene-by-eight-track block
of clips, giving you a matrix of 64 scenes by 64 tracks. Hit a pad to focus on that section of the
Session View. For example, holding the Shift button and then pressing the pad in row three, column
one will put the focus on scenes 17-24 and tracks 1-8. Furthermore, while Shift is held, each scene
launch button represents a block of 64 scenes, if they are available in your Set.

In the Session Overview, the color coding is a little different:

•

•

Amber: indicates the currently selected block of clips, which will be surrounded by the colored
border in the software.
Green: there are clips playing in that block of clips (though that may not be the block of clips
selected).

•
•

Red: there are no clips playing in that range.
No color: there are no tracks or scenes in that range.

32.14 Setting User Preferences

Press and hold the User button to adjust the sensitivity of Push 1’s velocity response, aftertouch, and
other settings.

User Button

User Settings

Pad Threshold sets the softest playing force that will trigger notes. More force is required at higher
settings. Note that at lower settings, notes may trigger accidentally and pads may “stick” on.

Velocity Curve determines how sensitive the pads are when hit with various amounts of force, and
ranges from Linear (a one-to-one relationship between striking force and note velocity) to various
logarithmic curves. Higher Log values provide more dynamic range when playing softly. Lighter
playing styles may benefit from higher Log values. The diagram below demonstrates the various
velocity curves, with striking force on the horizontal axis and note velocity on the vertical axis.

Diagram of Push 1’s Velocity Curves.

The Workflow option determines how Push 1 behaves when the Duplicate, New, or Up/Down arrow
buttons are pressed. Which mode you choose depends on how you like to organize your musical
ideas. In Scene Workflow (which is the default), musical ideas are organized and navigated in
scenes. In Clip Workflow, you’re working with only the currently selected clip.

In Scene Workflow:

•

•

•

Duplicate creates a new scene containing all of the currently playing clips, and seamlessly
switches to playing them back. This is the same as the Capture and Insert Scene command in
Live’s Create menu.
New is identical to Duplicate, except that it does not duplicate the currently selected clip.
Instead, an empty clip slot is prepared, allowing you to create a new idea in the current track.
The Up/Down Arrows move up or down by a single scene. Playback of the clips in the new
scene begins seamlessly.

In Clip Workflow:

•

•

Duplicate creates a copy of the currently selected clip in the next clip slot, while continuing
playback of any currently playing clips in other tracks. Hold Shift while pressing Duplicate to
create a new scene containing all of the currently playing clips.
New prepares an empty clip slot on the currently selected track. Clips in other tracks are not
affected.

•

the Up/Down Arrows move up or down by a single scene. Playback of the currently selected
track’s clip in the new scene begins seamlessly. Clips in other tracks are not affected.

Aftertouch Threshold sets the lowest incoming aftertouch value (from 0-127) that Push will register.
Input values below this level will be ignored, while input values above this level will be scaled across
the entire aftertouch range. For example, if you set the Aftertouch Threshold to 120 and play with an
aftertouch value of 119, nothing will happen. But input values between 120 and 127 will be scaled to
output a value from 0 to 127, as follows:

120 -> 0
121 -> 18
122 -> 36
123 -> 54
124 -> 72
125 -> 90
126 -> 108
127 -> 127

32.15 Push 1 Control Reference

The function of each section and control is explained below.

32.15.0.1 Focus/Navigation Section

Focus/Navigation Section.

Note Mode — When selected, the Pad Section changes its functionality based on the type of track
that is currently selected:

•

MIDI track containing an instrument — the pads plays notes. Pressing Note additional times
toggles between real-time playing and melodic step sequencing.

•

MIDI track containing a Drum Rack — the Pad Section is divided; the lower-left 16 pads play
the Drum Rack, the lower-right 16 pads adjust the loop length of the clip, and the upper four
rows control the step sequencer. Press Note again to toggle to 64-pad mode, allowing you to
play drums across the entire 8x8 pad grid.

Session Mode — When selected, the Pad Section changes to launch clips in Live’s Session View.

Shift — Press and hold Shift while pressing other buttons to access additional functionality.

Arrow Keys — Move through your Live Set (in Session Mode) and between tracks or scenes/clips (in
Note Mode).

Select — In Session Mode, hold Select and press a clip to select the clip without launching it. This will
also display the clip name in the display. In Note Mode, hold Select and press a Drum Rack pad to
select its notes without triggering the pad.

32.15.0.2 Add Section

Add Section.

These buttons add new devices or tracks to your Live Set.

Add Effect — Opens Browse Mode to add a new device to the right of the currently selected device.
Hold Shift while pressing Add Effect to add the new device to the left of the currently selected device.
To add a MIDI Effect, first select the instrument in a track. Then hold Shift while pressing Add Effect.

Add Track — Creates a new MIDI track to the right of the currently selected track. Press and hold Add
Track to select a different type of track to add, i.e., Audio, MIDI, or Return. If the Add Track button is
pressed while a track within a Group Track is selected, any new tracks will be inserted into that Group
Track.

32.15.0.3 Note Section

Note Section.

These buttons adjust how notes are played on Push 1.

Scales — When Note Mode is on and an instrument track is selected, pressing this button allows you
to select which scale will be played on the pads. Note that this button has no effect when a Drum
Rack track is selected or when in Session Mode.

•

•

•

Fixed Y/N: When Fixed Mode is on, the notes on the pad grid remain in the same positions
when you change keys; the bottom-left pad will always play C, except in keys that don’t
contain a C, in which case the bottom-left pad will play the nearest note in the key. When Fixed
is off, the notes on the pad grid shift so that the bottom-left pad always plays the root of the
selected key.
In Key/Chromatic: With In Key selected, the pad grid is effectively “folded” so that only notes
within the key are available. In Chromatic Mode, the pad grid contains all notes. Notes that are
in the key are lit, while notes that are not in the key are unlit.
Scale selection: Select the base scale with the up/down buttons on the lefthand side.

User — All of Push 1’s built-in functionality can be disabled via User Mode. This allows Push 1 to be
reprogrammed to control alternate functions in Live or other software. Press and hold the User button
to access a number of configuration options. Push 1’s relative encoders work best in “Relative (2’s
Comp.)” mode. To ensure this mode is selected, turn the encoder slowly to the left during mapping.

Repeat — When Repeat is enabled, holding down a pad will retrigger the note. The Scene/Grid
buttons change the rhythmic value of the repeated note.

Accent — When Accent is enabled, all incoming notes (whether step sequenced or played in real-
time) are played at full velocity. Press and hold Accent to temporarily enable it.

Octave Up/Down — If an instrument track is selected, these buttons shift the pads up or down by
octave. If a Drum Rack is selected, these buttons shift the Drum Rack’s pad overview up or down by
16 pads. In Session Mode, these buttons shift control of the Session View up or down by eight scenes.
These buttons will be unlit if no additional octaves are available.

32.15.0.4 State Control Section

State Control Section.

When working with tracks, the leftmost eight buttons will either stop clips or mute or solo the
corresponding track, depending on which of the three rightmost buttons is pressed (Stop, Mute, or
Solo). When working with devices instead of tracks, the leftmost eight buttons will toggle devices on
and off. These buttons have additional functionality in other modes, e.g., scale selection.

To stop all clips, press and hold Shift, and then press Stop.

32.15.0.5 Selection Control Section

Selection Control Section.

These buttons work in conjunction with the Display/Encoder Section buttons and select what
parameters can be edited by the encoders and shown in the display. The In and Out buttons allow
you to access devices inside Racks or additional parameter banks for devices with more than eight
parameters. In Browse Mode, the In and Out buttons shift the display to the right or left, allowing you
to browse deeper levels of subfolders or view a larger number of presets on the display.

32.15.0.6 Display/Encoder Section

Display/Encoder Section.

The six buttons to the right of the display determine the editing mode of the encoders. In all modes, the
ninth encoder controls the volume of the Main track, or the Pre-Cue volume if Shift is held. Holding
Shift while adjusting any of the first eight encoders allows you to fine-tune whichever parameter is
currently being controlled by that encoder. Note that you can temporarily toggle to a different editing
mode by pressing and holding the corresponding button. Releasing the button will then return to the
previous mode.

Volume Mode.

In Volume Mode, the encoders control volume of the eight selected tracks.

Pan & Send Mode.

In Pan & Send Mode, press once to control pans. Subsequent presses cycle through sends.

Track Mode.

In Track Mode, the encoders control track volume, pan and the first six sends of the selected track.
Select which clip track to control via the eight Selection Control buttons. Press the Master button to
select the Main track.

In Clip Mode, the encoders control various parameters for the selected clip. The parameters depend
on the type of clip selected:

Clip Mode With a MIDI Clip Selected.

•
•
•
•

Loop Start (or Clip Start if Loop is off)
Position
Loop Length (or Clip End if Loop is off)
Loop On/Off

Clip Mode With an Audio Clip Selected.

•
•
•
•
•
•
•
•

Loop Start (or Clip Start if Loop is off)
Position
Loop Length (or Clip End if Loop is off)
Loop On/Off
Warp Mode
Detune
Transpose
Gain

Device — The encoders control parameters for the selected device.

Browse — The encoders scroll through the available devices and presets.

32.15.0.7 Tempo Section

Tempo Section.

Tap Tempo — As you press once every beat, the tempo of the Live Set will follow your tapping. If the
“Start Playback with Tap Tempo” button is enabled in Live’s Record, Warp & Launch Settings, you can
also use tapping to count in: If you are working in a 4/4 signature, it takes four taps to start song
playback at the tapped tempo.

Metronome — Toggles Live’s metronome on or off.

The left encoder adjusts Live’s tempo in increments of one BPM. Holding Shift while adjusting will set
the tempo in increments of .1 BPM.

The right encoder sets the amount of swing applied when Quantizing, Record Quantizing or when
Repeat is pressed.

32.15.0.8 Edit Section

Edit Section.

Undo — Undoes the last action. Press and hold Shift while pressing Undo to Redo. Note that Push 1’s
Undo button applies Live’s Undo functionality, so it will undo actions in your Live Set even if they were
done without using Push 1.

Delete — In Note Mode, this button deletes the selected clip. In Session Mode, hold Delete and then
press a clip to delete that clip. Hold Delete and select a device or track with Push 1’s Selection Control
buttons to delete. Hold Delete and touch an encoder to delete automation controlled by that encoder.
If automation has not been recorded for a particular parameter, holding Delete and touching the
corresponding encoder will reset that parameter to its default value.

Quantize — Press and release to quantize the selected notes (or all notes in the clip if there is no
selection). Hold Quantize and press a drum pad to quantize that pad’s notes. For audio clips,
Quantize will affect transients. Press and hold Quantize to access quantization settings. After
changing these settings, press once to exit and then press and release to apply your changes.

Double — doubles the material within the loop, as well as the length of the loop.

32.15.0.9 Transport Section

Transport Section.

Fixed Length — When enabled, all newly created clips will be a fixed number of bars. When
disabled, new clips will continue to record until you press the Record, New or Play/Stop buttons.
Press and hold, then use the buttons beneath the display to specify the fixed recording length.
Enabling Fixed Length while recording will switch recording off and loop the last few bars of the clip,
depending on the Fixed Length setting.

Automation — Toggles Live’s Automation Record button. When on, your parameter changes will be
recorded into playing Session View clips. Hold Shift and press Automation to reenable any
automation that you have overridden. Hold Delete and press the Automation button to delete all
automation in a clip.

Duplicate — In Scene Workflow, Duplicate creates a new scene containing all of the currently playing
clips. In Clip Workflow, Duplicate creates a copy of the currently selected clip in the next clip slot,
while continuing playback of any currently playing clips in other tracks. Hold Duplicate while pressing
a Drum Rack pad to copy the pad and paste it to a new location in the Drum Rack.

New — Pressing New stops the selected clip and prepares Live to record new material. This allows
you to practice before making a new recording. On armed MIDI tracks, holding Record while
pressing New triggers Capture MIDI.

Record — Press the Record button to begin recording. Pressing Record again will stop recording but
will continue playing back the clip. Pressing Record a third time will enable overdub mode, allowing
you to record into the clip while it plays back.

Play/Stop — Toggles the play button in Live’s transport bar. Hold Shift while pressing Play/Stop to
return Live’s transport to 1.1.1 without starting playback.

32.15.0.10 Touch Strip

Touch Strip.

When an instrument track is selected, the touch strip adjusts pitch bend or modulation wheel amount
when playing in real-time, or the available range of notes when step sequencing. When a Drum Rack
track is selected, the touch strip selects the Drum Rack bank.

Pitch bend is selected by default when an instrument track is selected. To change the functionality of
the touch strip, hold Select and tap the strip. This toggles between pitch bend and mod wheel
functionality each time you tap it. The display will briefly show the current mode each time you change
it. Note that pitch bend and modulation wheel functionality is only available when playing instruments
in real time, and not when using the melodic step sequencers.

32.15.0.11 Pad Section

Pad Section.

The functionality of the Pad Section is determined by the Note and Session Mode buttons. When
Session Mode is on, the Pad Section is used to launch clips in Live’s Session View. When Note Mode
is on, the Pad Section changes its functionality based on the type of track that is currently selected:

•

•

MIDI track containing an instrument — the pads plays notes. Pressing Note additional times
toggles between real-time playing and melodic step sequencing.
MIDI track containing a Drum Rack — the Pad Section is divided; the lower-left 16 pads play
the Drum Rack, the lower-right 16 pads adjust the loop length of the clip, and the upper four
rows control the step sequencer. Press Note again to toggle to 64-pad mode, allowing you to
play drums across the entire 8x8 pad grid.

32.15.0.12 Scene/Grid Section

Scene/Grid Section.

These buttons also change their functionality depending on whether Session Mode or Note Mode is
selected. When Session Mode is selected, these buttons launch Session View scenes. Hold the Select
button while pressing a Scene button to select the scene without launching it. When Note Mode is
selected, the Scene/Grid Section determines the rhythmic resolution of the step sequencer grid and
the rhythmic resolution of repeated notes when Repeat is enabled.

32.15.0.13 Using Footswitches with Push 1

Two ports on the back of Push 1 allow you to connect momentary footswitches. Footswitch 1 acts as a
sustain pedal. Footswitch 2 gives you hands-free control of Push 1’s recording functionality. A single
tap of the footswitch will toggle the Record button, thus switching between recording/overdubbing
and playback of the current clip. Quickly double-tapping the footswitch is the same as pressing the
New button.

Note that certain footswitches may behave “backwards”; for example, notes may sustain only when
the pedal is not depressed. Footswitch polarity can usually be corrected by connecting the footswitch
to the port while depressing it, but we recommend using footswitches with a physical polarity switch.

33. Using Push 2

Ableton Push 2 is an instrument for song creation that provides hands-on control of melody and
harmony, beats, samples, sounds, and song structure. In the studio, Push 2 allows you to quickly
create clips that populate Live’s Session View as you work entirely from the hardware. On stage, Push
2 serves as a powerful instrument for real-time playing, step sequencing, and clip launching.

Overview of Push 2’s Controls.

Much of Push 2’s behavior depends on which mode it is in, as well as on which type of track is
selected. To help you learn how to work with Push 2, this chapter will walk you through some of the
fundamental workflows, and then will provide a reference of all of Push 2’s controls.

There are also a number of videos that will help you get started with Push 2. These are available at
https://www.ableton.com/learn-push/

33.1 Setup

After plugging in the included power supply and connecting the USB cable to your computer, turn
Push 2 on via the power button in the back. From here, setting up the Push 2 hardware is mostly
automatic. As long as Live is running, Push 2 will be automatically detected as soon as it is connected
to a USB port on your computer. After connection, Push 2 can be used almost immediately. It is not
necessary to install drivers and Push 2 does not need to be manually configured in Live’s Settings.

From time to time, Ableton will release firmware updates for Push 2 that will be included in updates to
Live. When using Push 2 for the first time after installing a new version of Live, you may be prompted
to update the firmware. Push 2 will walk you through this process.

33.2 Browsing and Loading Sounds

You can browse and load sounds directly from Push 2, without needing to use Live’s browser. This is
done in Push 2’s Browse Mode.

Press Push 2’s Browse button:

The Browse Button.

The display is divided into columns. When you first enter Browse Mode, the far left column shows
either the specific category of device being browsed or the Collections label, which lets you access
tagged browser items quickly. Each column to the right shows the next subfolder (if any exist) or the
contents of the current folder. You can scroll through presets and folders using the eight encoders
above the display, or navigate through them one at a time via the arrow buttons.

Arrow Buttons.

The display will expand automatically as you navigate. You can load Live’s “default” devices from the
top level of the browser’s hierarchy, and can quickly move up or down in the hierarchy via the
rightmost two upper display buttons.

Navigate Up and Down in the Browser Hierarchy.

By default, samples and presets from official Packs or Live’s Core Library will preview when selected in
the browser. You can toggle preview on or off via the Preview button.

Preview Button.

To adjust the previewing volume, hold the Shift button while turning the Master volume encoder.

Shift Button.

Master Volume Encoder.

To load the selected item, press the Load button.

Loading Items in Browse Mode.

What you see when in Browse Mode depends on the device that was last selected. If you were
working with an instrument, Browse Mode will show you replacement instruments. If you were
working with an effect, you will see effects. When starting with an empty MIDI track, the display
shows all of your available sounds, instruments, drum kits, effects, and Max for Live devices, as well as
VST and Audio Unit plug-ins.

33.3 Playing and Programming Beats

To create beats using Push 2, first make sure Note Mode is enabled

The Note Mode Button.

Then use Browse Mode to navigate to the Drums section of the browser and load one of the Drum
Rack presets from Live’s library.

When working with a MIDI track containing a Drum Rack, Push 2’s 8x8 pad grid can be configured in
a few different ways, depending on the state of the Layout button. Pressing this button cycles between
three different modes.

The Layout Button

33.3.1 Loop Selector

When the Loop Selector layout is enabled, the pads are divided into three sections, allowing you to
simultaneously play, step sequence and adjust the length of your clip.

The Pad Grid with the Loop Selector Layout

The 16 Drum Rack pads are laid out, like Live’s Drum Rack, in the classic 4x4 arrangement, allowing
for real-time playing. Controls in the display and the pads in the Drum Rack match the color of the
track, with subtle variations that help you understand what’s happening. The Drum Rack pad colors
indicate the following:

•
•
•
•
•
•

The track’s color — this pad contains a sound.
Lighter version of the track’s color — this pad is empty.
Green — this pad is currently-playing.
White — this pad is selected.
Dark blue — this pad is soloed.
Gray— this pad is muted.

When working with Drum Racks that contain a larger number of pads, use Push 2’s touch strip or the
Octave Up and Octave Down buttons to move up/down by 16 pads. Hold Shift while using the
touch strip or Octave buttons to move by single rows.

Octave Up/Down Buttons.

Holding the Layout button gives you momentary access to the 16 Velocities layout. You can also lock
the alternate layout in place by holding Shift and pressing the Layout button. To unlock the 16
Velocities layout, press the Layout button again.

33.3.2 16 Velocities Mode

Press the Layout button to switch to the 16 Velocities layout. In this mode, the bottom right 16 pads
represent 16 different velocities for the selected Drum Rack pad. Tap one of the velocity pads to enter
steps at that velocity.

The Pad Grid with the 16 Velocities Layout

Holding the Layout button gives you momentary access to the loop length controls. You can also lock
the loop length controls in place by holding Shift and pressing the Layout button. To unlock the loop
length pads, press the Layout button again.

33.3.3 64-Pad Mode

You can also use the entire 8x8 pad grid for real-time drum playing. This is useful when working with
very large drum kits, such as those created by slicing. To switch to 64-pad mode, press the Layout
button again.

When moving between 64-pad mode and the Loop Selector or 16 Velocities layouts, the 16 pads
available for step sequencing will not change automatically. You may still need to use the touch strip
or Octave keys in order to see the specific 16 pads you want.

Holding the Layout button gives you momentary access to the loop length controls. You can also lock
the loop length controls in place by holding Shift and pressing the Layout button. To unlock the loop
length pads, press the Layout button again.

33.3.4 Loading Individual Drums

Browse Mode can also be used to load or replace individual pads within a loaded Drum Rack. To
switch between browsing Drum Racks and single pads, make sure you’re in Device Mode by pressing
the Device button. This will show the devices on the track.

Device Button.

By default, the Drum Rack is selected. To select an individual pad instead, tap that pad, then press the
second upper display button. The square icon next to the name represents a pad.

Selecting an Individual Pad in a Drum Rack.

Now, entering Browse Mode again will allow you to load or replace the sound of only the selected
pad. The selected pad will flash. Once in Browse Mode, tapping other pads will select them for
browsing, allowing you to quickly load or replace multiple sounds within the loaded Drum Rack.

After loading the selected item, the Load button’s name will change to Load Next. Pressing this button
again will load the next entry in the list, allowing you to quickly try out presets or samples in the
context of your song. You can also load the previous entry in the list via the Load Previous button.

Particularly in a performance situation, you may want to select a pad without triggering it. To do this,
press and hold the Select button while tapping a drum pad or one of the 16 Velocity pads.

Select Button.

You can also select without triggering by pressing the lower display button for the Drum Rack’s track.
This will expand the Drum Rack and allow the individual pads to be selected via the other lower
display buttons. You can navigate to the previous or next pad via the left and right arrow keys.

Press the Drum Rack’s Lower Display Button to Access Individual Pads.

33.3.4.1 Additional Pad Options for Push 2

To copy a pad to a different location in your Drum Rack, hold the Duplicate button and press the pad
you’d like to copy.

Duplicate Button.

While continuing to hold Duplicate, press the pad where you’d like to paste the copied pad. Note that
this will replace the destination pad’s devices (and thus its sound) but will not replace any existing
notes already recorded for that pad.

When a single pad is selected, you can adjust its choke group assignment via the first encoder or
transpose the pad via the second encoder.

Assign a Pad to a Choke Group or Transpose the Pad.

When working with drums, Push 2’s pads can be colored individually. To change a pad’s color, hold
Shift and tap the pad. Then tap one of the pads on the outer ring to choose that color for the selected
pad.

Your custom pad colors will be saved and reloaded with your Live Set, but will not be visible within
Live. They only appear on Push 2.

Choose a Color for a Drum Pad.

33.3.5 Step Sequencing Beats

Tapping a pad selects it and also enables it for step sequencing.

To record notes with the step sequencer, tap the pads in the step sequencer controls to place notes in
the clip where you want them. The clip will begin playing as soon as you tap a step. By default, each
step sequencer pad corresponds to a 16th note, but you can change the step size via the Scene/Grid
buttons.

Scene/Grid Buttons.

Adjust the tempo using the Tempo encoder. Each click of the encoder will adjust the tempo in
increments of one BPM. Holding Shift while adjusting will set the tempo in increments of .1 BPM.

Adjust the Tempo with the Tempo Encoder.

As the clip plays, the currently playing step is indicated by the moving green pad in the step
sequencer section. When Record is enabled, the moving pad will be red. Tapping a step that already
has a note will delete that note. Press and hold the Mute button while tapping a step to deactivate it
without deleting it. Press and hold the Solo button while tapping a pad to solo that sound.

Mute and Solo Buttons.

You can also adjust the velocity and micro-timing of individual notes, as described in the section on
step sequencing automation.

To delete the entire pattern, press the Delete button. To delete all notes for a single pad, press and
hold Delete while tapping that pad. Holding Delete while pressing a pad that has no notes recorded
in the current pattern deletes all of the devices from that pad.

Delete Button.

The pad colors in the step sequencer section indicate the following:

•
•
•
•

Gray — this step doesn’t contain a note.
The clip’s color — this step contains a note. Higher velocities are indicated by brighter pads.
Lighter version of the clip’s color — this step contains a note, but the note is muted.
Unlit — the right two columns of pads will be unlit if triplets are selected as the step size. In this
case, these pads are not active; only the first six pads in each row of steps can be used.

When Triplets are Selected, the Unlit Steps are Unavailable.

For detailed information about adjusting the loop length pads, see the section called Adjusting the
Loop Length.

33.3.6 Real-time Recording

Drum patterns can also be recorded in real-time by playing the Drum Rack pads. Follow these steps to
record in real-time:

•

If you want to record with a click track, press the Metronome button to enable Live’s built-in
click. You can adjust the metronome volume by holding the Shift button while adjusting the
Master volume encoder. As with all of the buttons on Push 2 that turn something on or off, when
the metronome is on, its button light will pulse.

Metronome Button.

•

Then Press the Record button to begin recording.

Record Button.

If you’ve enabled a recording count-in in Live, you’ll see a countdown bar move across the top of
Push 2’s display and flash in tempo. This can serve as a helpful visual reference for when to begin
playing.

Count-In Bar in Push 2’s Display

Now any Drum Rack pads you play will be recorded to the clip. Pressing Record again will stop
recording but will continue playing back the clip. Pressing Record a third time will enable overdub
mode, allowing you to record into the clip while it plays back. Subsequent presses continue to toggle
between playback and overdub. During playback, a small progress bar will appear in the display to
show the playback position of each playing clip.

The pads are velocity sensitive, but if you want to temporarily override the velocity sensitivity, press the
Accent button. When Accent is enabled, all played or step-sequenced notes will be at full velocity
(127), regardless of how hard you actually tap the pads.

Enable Accent to Play or Record at Full Velocity.

If you press and release Accent quickly, the button will stay on. If you press and hold, the button will
turn off when released, allowing for momentary control of accented notes.

In 16 Velocities mode, you can tap one of the 16 velocity pads to record the selected sound at that
velocity. Note that Accent overrides this behavior.

Pressing New stops playback of the currently selected clip and prepares Live to record a new clip on
the currently selected track. This allows you to practice before recording a new idea. By default,
pressing New also duplicates all clips that are playing on other tracks to a new scene and continues
playing them back seamlessly. This behavior can be changed by changing the Workflow mode in
Push 2’s Setup menu.

New Button.

33.3.7 Fixed Length Recording

Press the Fixed Length button to set the size of new clips to a predetermined length.

Fixed Length Button.

Press and hold Fixed Length to set the recording length.

Fixed Length Recording Options.

When Fixed Length is disabled, new clips will continue to record until you press the Record, New or
Play/Stop buttons.

By default, starting a recording with Fixed Length enabled will create an empty clip of the selected
length, and then begin recording from the beginning of the clip, in accordance with Live’s global
launch quantization. If Phrase Sync is enabled, Push 2 treats the chosen length as a musical phrase,
and will begin recording from the position in the clip that corresponds to that position within a phrase
of that length. For example, with a fixed length of 4 bars and Phrase Sync on, starting a recording
when Live’s global transport is at bar 7 will create an empty four bar clip and begin recording at the
third bar of that clip.

Enabling Fixed Length while recording will switch recording off and loop the last few bars of the clip,
depending on the Fixed Length setting.

33.4 Additional Recording Options

33.4.1 Recording with Repeat

With Push 2’s Repeat button enabled, you can hold down a pad to play or record a stream of
continuous, rhythmically-even notes. This is useful for recording steady hi-hat patterns, for example.
Varying your finger pressure on the pad will change the volume of the repeated notes.

Repeat Button.

The repeat rate is set with the Scene/Grid buttons. Note that Push 2 “remembers” the Repeat button’s
state and setting for each track. If you press and release Repeat quickly, the button will stay on. If you
press and hold, the button will turn off when released, allowing for momentary control of repeated
notes.

Turn up the Swing knob to apply swing to the repeated notes. When you touch the knob, the display
will show the amount of swing.

Swing Knob.

33.4.2 Quantizing

Pressing Push 2’s Quantize button will snap notes to the grid in the selected clip.

Quantize Button.

Press and hold Quantize to change the quantization options:

Quantization Options.

Swing Amount determines the amount of swing that will be applied to the quantized notes. Note that
the Swing amount can be adjusted from Encoder 1 or from the dedicated Swing knob.

Quantize To sets the nearest note value to which notes will be quantized, while Quantize Amount
determines the amount that notes can be moved from their original positions.

Enable Record Quantize by pressing the corresponding upper display button to automatically
quantize notes during recording. Adjust the record quantization value with Encoder 5. Note that if
Record Quantize is enabled and Swing is turned up, the automatically quantized notes will not have
swing applied.

When working with drums, press and hold Quantize and press a Drum Rack pad to quantize only that
drum’s notes in the current clip.

33.4.3 Arrangement Recording

When Live’s Arrangement View is in focus in the software, pressing Record will toggle Arrangement
Recording on and off. While Arrangement Recording is on, all of your actions on Push 2 are recorded
into the Arrangement View.

You can also trigger Arrangement Recording while Live’s Session View is in focus by holding Shift and
pressing Record. Note that this behavior is reversed when the Arrangement is in focus; holding Shift
and pressing Record will then toggle Session recording.

33.5 Playing Melodies and Harmonies

After working on a beat, you’ll want to create other elements such as a bassline, harmony parts, etc. If
you already have additional tracks in your Set, you can switch between them using the lower display
buttons or the left and right arrow keys.

Switch Between Tracks with the Lower Display Buttons.

Or you can add a new track by pressing the Add Track button.

Add Track Button.

Adding a track puts Push 2 into Browse mode, allowing you to select which type of track you’d like to
add (MIDI, Audio, or Return) and optionally load a device to the new track at the same time.

Choose a Track Type and Optionally Load A Device.

Note that when pressing the Add Track button while a track within a Group Track is selected, any new
tracks will be inserted into that Group Track.

After creating a track, you can change its color. To do this, hold Shift and press the lower display
button for the track. Then tap one of the pads on the outer ring to choose that color for the selected
track.

When working with a MIDI track containing an instrument, Push 2’s 8x8 pad grid automatically
configures itself to play notes. By default, every note on the grid is in the key of C major. The bottom
left pad plays C1 (although you can change the octave with the Octave Up and Down buttons).
Moving upward, each pad is a fourth higher. Moving to the right, each pad is the next note in the C
major scale.

Play a major scale by playing the first three pads in the first row, then the first three pads in the next
row upwards. Continue until you reach the next C:

C Major Scale.

The pad colors help you to stay oriented as you play:

•
•
•
•

The track’s color — this note is the root note of the key (e.g., C).
White — this note is in the scale, but is not the root.
Green — the currently-playing note (other pads will also turn green if they play the same note).
Red — the currently-playing note when recording.

To play triads, try out the following shape anywhere on the grid:

C Major Chord.

Holding the Layout button gives you momentary access to the loop length controls. You can also lock
the loop length controls in place by holding Shift and pressing the Layout button. To unlock the loop
length pads, press the Layout button again.

33.5.1 Playing in Other Keys

Press Push 2’s Scale button to change the selected key and/or scale.

Scale Button.

Using the upper and lower display buttons, you can change the key played by the pad grid. The
currently selected key appears in white, while the other key options appear in gray:

By default, the pads and scale selection options indicate major scales. You can change to a variety of
other scale types using encoders 2 through 7. The selected scale type is highlighted.

Key, Scale, and Layout Options.

In addition to changing the key, you can also change the arrangement of the grid in a number of
ways:

The Layout (Encoder 1) and Direction (Encoder 8) controls work together to determine the orientation
of the pad grid. The default settings are a Layout of “4ths” and a Direction of “Vert.” In this
configuration, each pad is a 4th higher than the pad directly below it. Changing the Layout to “3rds“
means that each pad is now a 3rd higher than the pad directly below it. The “Sequent” layout puts all
notes sequentially in order. This layout is useful if you need a very large range of notes available,
because it has no duplicated notes.

Changing the Direction control to “Horiz.” rotates the pad grid 90 degrees. For example, with a
Layout of “4ths,” each pad is a 4th higher than the pad to its left.

Fixed Off/On: The lower right display button toggles Fixed on or off. When Fixed is on, the notes on
the pad grid remain in the same positions when you change keys; the bottom-left pad will always play
C, except in keys that don’t contain a C, in which case the bottom-left pad will play the nearest note in
the key. When Fixed is off, the notes on the pad grid shift so that the bottom-left pad always plays the
root of the selected key.

In Key/Chromatic: The lower left display button toggles between In Key and Chromatic. With In Key
selected, the pad grid is effectively “folded” so that only notes within the key are available. In
Chromatic Mode, the pad grid contains all notes. Notes that are in the key are lit, while notes that are
not in the key are unlit.

Scale options are saved with the Set, and Push 2 will return to these settings when the Set is loaded
again. If you have particular key and scale settings that you like to use all the time, you can save them
in your Default Set. Any new Set created after this will have those settings in place when working with
Push 2.

All of the real-time recording options available for drums are also available for melodies and
harmonies, including the Accent button, fixed length recording, recording with repeat, and quantizing.
But for detailed editing, you’ll work with the Melodic Sequencer described in the next section.

One editing possibility is available in the real-time Note Mode: to quickly delete all notes of the same
pitch within the current loop, press and hold Delete and then tap the respective pad.

33.6 Step Sequencing Melodies and Harmonies

In addition to playing and recording in real time, you can also step sequence your melodies and
harmonies. To toggle to the Melodic Sequencer, press the Layout button. This will set the 8x8 pad grid
as follows:

The Pad Grid When Step Sequencing Pitches.

When using the Melodic Sequencer, all eight rows of pads allow you to place notes in the clip. You
can adjust the loop length and access additional step sequencing pages via the loop length pads. The
loop length pads can be momentarily accessed in the top row while holding the Layout button.

You can also lock the loop length pads in place. To do this, hold Shift and tap the Layout button. Note
that Push remembers this locked/unlocked state for each track. To unlock the loop length pads, press
the Layout button again.

With In Key selected, each row corresponds to one of the available pitches in the currently selected
scale. With Chromatic selected, notes that are in the key are lit, while notes that are not in the key are
unlit. The white row (which is the bottom row by default) indicates the root of the selected key. Each
column of pads represents a step in the resolution set by the Scene/Grid buttons.

As with the real-time playing layout, pressing the Octave Up or Down button shifts the range of
available notes. You can also use the touch strip to change the range. Hold the Shift key while
adjusting the touch strip to shift the range by octaves. Hold the shift key while pressing the Octave
buttons to shift by one note in the scale. The display will briefly show the available range as you adjust
it.

Additionally, brightly-lit touch strip lights indicate the currently available note range, while dimly-lit
touch strip lights indicate that the clip contains notes within the corresponding note range.

Pressing Layout again will toggle to the Melodic Sequencer + 32 Notes layout.

In addition to adding and removing notes, you can also adjust the velocity and micro-timing of the
notes, as described in the section on step sequencing automation.

33.6.1 Adjusting the Loop Length

The loop length controls allow you to set the length of the clip’s loop and determine which part of it
you can see and edit in the melodic and drum step sequencers. Each loop length pad corresponds to
a page of steps, and the length of a page depends on the step resolution. When working with drums
at the default 16th note resolution, two pages of steps are available at a time, for a total of two bars.
In the Melodic Sequencer layout, one page of eight steps is available at a time, for a total of two
beats. To change the loop length, hold one pad and then tap another pad, or, to set the loop length to
exactly one page, quickly double-tap the corresponding pad.

Each Loop Length Pad Corresponds to One Page.

Note that the page you see is not necessarily the page you hear. When you set the loop length, the
pages will update so that the current play position (as indicated by the moving green pad in the step
sequencer section) always remains visible. But in some cases, you may want to disable this auto-
follow behavior. For example, you may want to edit a single page of a longer loop, while still
allowing the loop to play for the length you set. To do this, single-tap the pad that corresponds to that
page. This will “lock” the view to that page without changing the loop length. You can also navigate
to the previous or next page by pressing the Page Left/Right buttons.

The Page Left/Right Buttons.

To then turn auto-follow back on, simply reselect the current loop. Note that single-tapping a page
that is outside of the current loop will immediately set the loop to that page. You can also turn auto-
follow back on by holding either one of the Page Left/Right buttons.

The pad colors in the loop length section indicate the following:

•
•
•
•
•

Unlit — this page is outside of the loop.
Gray — this page is within the loop, but is not currently visible in the step sequencer section.
White — this page is visible in the step sequencer section, but is not currently playing.
Green — this is the currently playing page.
Red — this is the currently recording page.

If you need to access the loop length pads frequently, you can lock them in place. To do this, hold
Shift and tap the Layout button. Note that Push remembers this locked/unlocked state for each track.
To unlock the loop length pads, press the Layout button again. You can also navigate to the previous
or next page by pressing the Page Left/Right buttons.

To duplicate the contents of a sequencer page, hold Duplicate, press the loop length pad for the page
you want to duplicate, and then press the loop length pad for the destination page. Note that this will
not remove existing notes in the destination page, but will add copied notes on top. To remove notes
first, hold Delete and tap the loop length pad for that page.

33.7 Melodic Sequencer + 32 Notes

The Melodic Sequencer + 32 Notes layout combines both step sequencing and real-time playing
capabilities. Providing access to multiple octaves and steps on a single page, this layout is ideal for
figuring out chords and harmonies to sequence. It is also well suited to longer phrases.

The Pad Grid with the Melodic Sequencer + 32 Notes Layout.

33.7.1 32 Notes

The bottom half of the pad grid lets you play notes in real-time, and select them for step sequencing.
Each pad corresponds to one of the available pitches in the currently selected scale. Pressing a pad
will select and play the note. Selected notes are represented by a lighter version of the track’s color.

To select a pad without triggering it, press and hold the Select button while tapping a pad.

The pad colors indicate the following:

•
•
•
•

The track’s color — this note is the root note of the scale.
Lighter version of the track’s color — this pad is selected.
Green — this pad is currently playing.
White — this note is in the scale, but is not the root.

Pressing the Octave Up or Down button shifts the range of available notes. Holding the Shift key while
adjusting the touch strip shifts the range by octaves. You can hold the Shift key while pressing the
Octave buttons to shift by one note in the scale. The display will briefly show the available range as
you adjust it.

As with the 64 Notes layout, the notes in the bottom half of the pad grid can be adjusted via the Scale
menu.

33.7.2 Sequencer

Tapping a step in the top half of the pad grid adds all selected notes to that step. Steps containing
notes are lit in the color of the clip.

Holding a step lets you view notes contained within the step, which are indicated in the bottom half of
the pad grid by the lighter version of the track’s color. Tapping any of these selected notes will remove
it from the step.

Holding multiple steps will add selected notes to all those steps. While holding Duplicate, you can
press a step to copy the notes in that step and then press another step to paste them to a new location
in the step sequencer.

The pad colors in the step sequencer indicate the following:

•
•
•
•
•
•

The clip’s color — this step contains a note.
Green — this step is currently playing.
White — this step is selected.
Light gray — this step contains a note, but the note is muted.
Gray — this pad is empty.
Unlit — the right two columns of pads will be unlit if triplets are selected as the step size. In this
case, these pads are not active; only the first six pads in each row of steps can be used.

Loop Length Pads in the Melodic Sequencer + 32 Notes Layout.

You can adjust the loop length and access additional step sequencing pages via the loop length
pads. The loop length pads can be momentarily accessed in the fifth row while holding the Layout
button.

The Layout Button.

You can also lock the loop length pads in place. To do this, hold Shift and tap the Layout button. Note
that Push remembers this locked/unlocked state for each track. To unlock the loop length pads, press
the Layout button again. You can also navigate to the previous or next page by pressing the Page
Left/Right buttons.

The Page Left/Right Buttons.

To duplicate the contents of a sequencer page, hold Duplicate, press the loop length pad for the page
you want to duplicate, and then press the loop length pad for the destination page. Note that this will

not remove existing notes in the destination page, but will add copied notes on top. To remove notes
first, hold Delete and tap the loop length pad for that page.

33.8 Working with Samples

Push 2 allows you to play samples from the pads in a variety of ways, with detailed but easy-to-use
control over sample parameters directly from the encoders and display. The instrument that powers
Push 2’s sample playback functionality is Simpler, and we recommend reading the detailed Simpler
chapter to learn more about its functionality.

To start working with a sample, you can either add a new MIDI track or press Browse to enter Browse
Mode on an existing MIDI track. Although you can load an empty Simpler to a track, it isn’t playable
until it contains a sample. Push 2’s display will inform you that your Simpler is empty and suggest
browsing for a sample:

Press Browse to Load a Sample in an Empty Simpler.

After loading a sample and switching to Device View, you will see the sample’s waveform in Push 2’s
display, along with a number of parameters that allow you to quickly adjust how the sample plays
back. This is the main bank of Simpler’s controls.

Simpler’s Main Parameter Bank in the Display.

By default, Simpler will automatically set certain parameters based on the length of the loaded
sample. For example, short samples will play once when triggered, while long samples will be set to
loop and warp. Warped samples will play back at the tempo of your Set, regardless of which note
you play. Bringing a warped clip into Simpler from an audio track, the browser, or your desktop
preserves any warp settings and markers that were in the original clip. For more information about
warping, see the Audio Clips, Tempo, and Warping chapter.

The most important parameter that determines how Simpler will treat samples is the Mode control,
which is used to choose one of Simpler’s three playback modes.

Simpler’s Mode Parameter.

•

•

•

Classic Playback Mode is the default mode when using Simpler, and is optimized for creating
“conventional” melodic and harmonic instruments using pitched samples. It features a complete
ADSR envelope and supports looping, allowing for samples to sustain as long as a note is held
down. Classic Mode is polyphonic by default, and the pad grid uses the same layout in this
mode as is used when playing other pitched instruments.
One-Shot Playback Mode is exclusively for monophonic playback, and is optimized for use
with one-shot drum hits or short sampled phrases. This mode has simplified envelope controls
and does not support looping. By default, the entire sample will play back when a note is
triggered, regardless of how long the note is held. The pad grid in One-Shot Mode also uses
the melodic layout.
Slicing Playback Mode non-destructively slices the sample so that the individual slices can be
played back from the pads. You can create and move slices manually, or choose from a
number of different options for how Simpler will automatically create slices. This mode is ideal
for working with rhythmic drum breaks.

33.8.1 Classic Playback Mode

Simpler’s Main Bank in Classic Mode.

In Classic Mode, the various sample position controls change which portion of the sample you play
back. For example, if you load a drum break that contains silence at the beginning, you can start
playback from after the silence. The Start control sets the absolute position in the sample from which
playback could start, while the End control sets where playback could end; these parameters define
the region of the sample that can be worked with. S Start and S Length are represented in
percentages of the total sample length enabled by Start and End. For example, hitting a pad after
setting an S Start value of 50% and S Length value of 25% will play back the third quarter (50-75%)
of the region between the Start and End values. S Loop Length determines how much of the available
sample (also determined by the Start and End values) will loop. Note that this parameter is only active
if Loop is enabled.

Adjust the Zoom encoder to zoom into a portion of the waveform. The display shows a representation
of the whole sample, as well as the currently active region. Turning the Zoom encoder clockwise
zooms in. The specific portion of the sample that you zoom to is determined by the last-touched
sample position control, e.g., Start, End, S Start, S Length.

Pressing Simpler’s upper display button will enter Edit Mode. When in Edit Mode, the lower display
buttons select additional pages of parameters and the upper display buttons toggle certain settings on
or off. Pressing Simpler’s upper display button again will exit Edit Mode.

Additional Parameters Available in Edit Mode.

Pressing the Loop On/Off button determines whether or not the sample will loop when a pad is held
down. The Warp as… button adjusts the warping of the sample between the Start and End values so
that it will play back precisely within the specified number of bars. Live makes its best guess about
what this value should be based on the length of the sample, but if it gets it wrong, you can use the ÷2
or ×2 buttons to double or halve the playback speed, respectively.

Crop removes the portions of the sample that are outside of the Start and End points, while Reverse
plays the entire sample backwards. Note that both Crop and Reverse are non-destructive; they create
a copy of the sample and apply the process to the copy, so your original sample is not changed.

33.8.2 One-Shot Mode

Simpler’s Main Bank in One-Shot Mode With Additional Edit Mode Controls.

In One-Shot Mode, the Zoom, Start, and End controls function the same as in Classic Mode, as do the
Warp as…, ÷2, ×2, Crop, and Reverse buttons.

With Trigger enabled, the sample will continue playing even after the pad is released; the amount of
time you hold the pad has no effect when Trigger is on. You can shape the volume of the sample using
the Fade In and Fade Out encoders. Fade In determines how long it takes the sample to reach its
maximum volume after a pad is hit, while Fade Out begins a fade out the specified amount of time
before the end of the sample region. To stop a one-shot sample immediately, hold Shift while pressing
the Play/Stop button.

With Gate enabled, the sample will begin fading out as soon as you release the pad. The Fade Out
time determines how long it will take to fade to silence after release.

The Transpose encoder allows you to transpose the sample up or down by up to 48 semitones (four
octaves). Note that when transposing, the timbre of the sample may change dramatically depending
on which Warp Mode you’ve selected. The Gain encoder sets the overall volume of the Simpler
instrument.

33.8.2.1 Legato Playback

Classic and One-Shot Modes provide a unique way of repitching a sample on the fly, without
changing its playback position. This is essentially a playable version of Legato Mode in clips. To
enable this functionality:

1.
2.
3.

In Edit Mode, press the second lower display button to view the Global parameter bank.
Set the Glide Mode parameter to Glide.
Set the Voices parameter to 1. Note that this parameter is only available in Classic Mode. In
One-Shot Mode, playback is always monophonic.

Now, as you play the pads legato, the sample will transpose without changing playback position. For
best results, make sure Warp is on (in the Warp parameter bank). The Complex Pro Warp Mode tends
to sound best when transposing, but experiment with the various Warp Modes to see which one works
best for your particular sample.

33.8.3 Slicing Mode

Simpler’s Main Bank in Slicing Mode With Additional Edit Mode Controls.

In Slicing Mode, the Zoom, Start, and End controls function the same as in Classic and One-Shot
Modes, as do the Warp as…, ÷2, ×2, and Reverse buttons.

The Slice By chooser determines the specific way in which slices will be created:

•

•

•

•

Transient - Slices are placed on the sample’s transients automatically. The Sensitivity encoder
determines how sensitive Simpler is to transient levels within the sample, and thus how many
slices will be automatically created. Higher numbers result in more slices, up to a maximum of
64 slices.
Beat - Slices are placed at musical beat divisions. The Division encoder selects the beat division
at which Simpler will slice the sample region.
Region - Slices are placed at equal time divisions. The Regions encoder selects the number of
evenly-spaced slices that will be created.
Manual - When Manual is selected, no slices are placed automatically. Instead, slices are
created manually by enabling Pad Slicing and tapping empty pads as the sample plays back.
To create manual slices:

1.
2.

3.

4.

Tap a pad that contains a slice to begin playback from that slice.
When the sample reaches the point at which you would like to create an additional slice (a
drum hit, for example), tap any empty pad.
A slice will be placed at this point and it will be assigned to a pad. Any pads that were already
assigned after this point will be shifted “upward” on the pad grid.
Once the loop is sliced as you like it, turn Pad Slicing off.

In all slicing modes, slices are laid out from left to right in groups of four starting from the bottom left
pad. Each additional four slices are placed on the next four pads up. After the left half of the pad grid
is used, slices are placed along the bottom row on the right side of the pad grid, again moving
upwards in groups of four.

Up to 64 Slices Can Be Created.

By default, the pad grid uses the 64-pad drum layout when in Slicing Mode. Pressing the Layout
button cycles between 64-pad, Loop Selector, and 16 Velocities modes.

The Playback encoder determines how many slices can be triggered simultaneously. Mono is
monophonic; only one pad can be played or sequenced at a time. When set to Poly, multiple pads
can be triggered together. When set to Through, playback is monophonic, but triggering one slice will
continue playback through the rest of the sample region.

The Trigger/Gate switch is the same concept as in One-Shot Playback Mode, but what you actually
hear depends on which Playback mode is selected.

Nudge allows you to adjust the position of each slice marker. This is especially useful for fine-tuning
slices that you’ve created in Manual mode. For greater nudging accuracy, tap the pad you’d like to
adjust and use the Zoom encoder to get a closer look. Hold Shift while adjusting Nudge for extremely
small adjustments.

Split Slice creates a new slice in the middle of the currently selected slice. This is also useful in Manual
mode, in conjunction with Nudge, for fine-tuning slices created via Pad Slicing.

To delete a slice (either manually or automatically created), hold Delete and tap the corresponding
pad.

33.9 Navigating in Note Mode

Now that you’ve created a few tracks, you can continue to add more. But you may want to move
between already-existing tracks to continue working on musical ideas using those instruments and
devices. You can move directly to a new track using the lower display buttons or move sequentially to
the previous or next track using the left and right arrow buttons.

Arrow Buttons.

Note that selecting a MIDI track on Push 2 automatically arms it, so it can be played immediately. In
Live, track Arm buttons will appear pink to indicate that they have been armed via selection.

Pink Track Arm Button.

You can also manually arm any track by holding the lower display button for that track, or by holding
the Record button and pressing the track’s lower display button.

This is useful if, for example, you want to use Push 2 to record audio clips. In Live, a manually armed
track’s track Arm button will appear red. On Push 2’s display, manually armed tracks appear with a
special icon.

Icon for a Manually Armed Track.

The specific behavior of the Up/Down Arrows is determined by the Workflow mode, which is set in
Push 2’s Setup menu. In both modes, the Up/Down Arrows move up or down by a single scene. In
Scene Workflow, the selected scene is triggered. In Clip Workflow, only the selected track’s clip is
triggered. Clips in other tracks are not affected.

Navigating with the Up/Down Arrows in Note Mode always begins playback immediately, and a
triggered clip will take over the play position from whatever clip was played in that track before. Note
that this is the same behavior as if the clips were set to Legato Mode in Live.

33.10 Working With Instruments and Effects

Pressing the Device button puts Push 2 in Device Mode, which allows you to use the encoders to
control parameters in Live’s devices and third-party plug-ins.

Device Button.

In Device Mode, the upper display buttons select devices in the currently selected track, enabling their
parameters for editing. The currently selected device is highlighted in the display.

Device Mode Settings.

Once a device is selected, pressing its upper display button again will enter Edit Mode. When in Edit
Mode, the lower display buttons select additional pages of parameters for the selected device.

Device Parameter Pages in Edit Mode.

When in Edit Mode, pressing the leftmost upper display button will take you back up to the Device
Mode’s top level.

Press the Leftmost Upper Display Button to Exit Edit Mode.

Certain devices, such as Live’s Operator instrument, have more than eight pages of parameters. When
working with these devices in Edit Mode, the rightmost lower display button will show an arrow. Press
this button to scroll to the additional pages and then press the leftmost lower display button to get
back.

Scroll to Additional Pages of Parameters.

33.10.1 Adding, Deleting, and Reordering Devices

To load additional devices such as MIDI or audio effects to a track, press the Add Device button. This
will open the Browser and display all device types that can be loaded to the current track.

Add Device Button.

You can also load an instrument via the Add Device button, but be aware that this works just like
Browse Mode: You will replace the instrument that’s already on the track.

As with Browse Mode, use the encoders or arrow keys to navigate between devices in the browser,
and the Load button to load the selected device or preset. Devices will load to the right of the
previously-selected device, although note that MIDI effects will always be placed before the
instrument in the track and audio effects will always be placed after it.

To delete a device, hold the Delete button and press the upper display button that corresponds to the
device.

Deleting a Device.

To disable a device (without deleting it), hold the Mute button and press the upper display button that
corresponds to the device. Disabled devices (and all of their parameters) appear gray in the display.

To re-enable a disabled device, hold Mute and again press the upper display button that corresponds
to the device.

Holding the Mute button for a few moments will lock it on. You can then release Mute and toggle
devices on and off just by pressing the corresponding upper display button. Press Mute again to
unlock it.

To move a MIDI or audio effect to a different position in the track’s chain of devices, press and hold
the upper display button that corresponds to the effect. Then use any of the eight encoders to scroll the
device to the new position and release the upper display button.

33.10.2 Working with Racks

Instrument, Drum, and Effect Racks allow for multiple chains of devices to be contained within a single
device. On Push 2’s display, Racks have special icons that distinguish them from regular devices.

A MIDI Effect Rack, an Instrument Rack, and an Audio Effect Rack.

A Drum Rack.

To open a Rack, select it using the corresponding upper display button. Then press this button again.
The Rack will unfold, revealing the devices in the currently selected chain. An unfolded Rack appears
in the display with an underline that extends to the end of the enclosed devices. Each press of a
selected Rack’s upper display button will toggle it open or closed. Note that Drum Racks cannot be
folded or unfolded directly from Push 2. They will appear in Push 2’s display as folded or unfolded
depending on how they were set within Live.

Expand a Rack to Access Its Devices.

When the Rack itself is selected, the eight encoders control the Rack’s Macro Controls. Once a Rack is
open, you can select one of its contained devices by pressing the relevant upper display button. After
selecting a different device, the encoders will then control its parameters instead.

The Encoders Adjust Parameters for the Selected Device.

To access the devices on additional chains within a multi-chain Rack, press and hold the Rack’s upper
display button. The Rack’s chains will be shown at the bottom of the display and can be selected via
the corresponding lower display buttons.

Selecting a Chain Within a Rack.

33.11 Track Control And Mixing

To control volumes, pans, or sends with the encoders, press the Mix button.

Mix Button.

Each press of the Mix button toggles between Track Mix Mode and Global Mix Mode. In Track Mix
Mode, the first two upper display buttons select between mix parameters for the selected track and
input and output routing options for that track. The lower display buttons are used to select the track.
With Mix selected, the encoders adjust volume, pan, and send levels for the currently selected track.

The Mix Controls in Track Mix Mode.

Hold Shift while adjusting the encoders for fine-tune control.

If your Set contains more than six return tracks, the two rightmost upper display buttons will change to
arrows, which allow you to shift the available parameters left or right.

Scroll to View Additional Sends.

With Input & Output selected, all of the track’s routing and monitoring options can be adjusted from
the encoders.

The Input and Output Settings in Track Mix Mode.

In Global Mix Mode, the encoders adjust either volumes, pans, or send levels for the eight visible
tracks. Select which parameter will be controlled via the upper display buttons.

Controlling the Pans for Eight Tracks.

If your Set contains more than six return tracks, the rightmost upper display button will change to an
arrow, which allows you to shift the available sends to the right. Volumes and Pans will always remain
visible.

If your Set contains more than eight tracks, the left and right arrow keys allow you to shift the visible
tracks left or right.

Press the Master button to select the Main track. Press Master again to return to the previously
selected track.

The Main Track Button.

Note that when Split Stereo Pan Mode is active while in Global Mix Mode, the display will show the
current pan value, but the pan dial will be disabled. In Track Mix Mode, the display will show either
the pan control or stereo pan sliders, depending on the active pan mode.

33.11.1 Rack and Group Track Mixing

On Push 2’s display, Group Tracks and tracks that contain Instrument or Drum Racks have special
icons that distinguish them.

A Group Track and Tracks Containing an Instrument Rack and a Drum Rack.

These types of tracks can be unfolded, allowing you to use the Mix Modes to control the tracks and
chains within them. To unfold one of these tracks, select it using the corresponding lower display
button. Then press this button again. The Group Track or Rack will unfold, revealing the enclosed
tracks or chains. An unfolded track appears in the display with an underline that extends to the end of
the enclosed tracks or chains. Each press of a selected track’s lower display button will toggle it open
or closed.

Expand a Group Track or Track Containing a Rack to Mix its Contents.

Use the left and right arrow keys to access additional chains or tracks that may have been pushed off
the display after unfolding. When working with an unfolded Drum Rack, hold Select and tap a pad to
jump to that pad in the mixer. This can make it easier to mix with a large Drum Rack.

33.12 Recording Automation

Changes that you make to device and mixer parameters can be recorded to your clips as automation,
so that the sound will change over time as the clip plays. To record automation, press Push 2’s
Automation button so that it turns red.

Automation Button.

This toggles Live’s Session Automation Arm button, allowing you to record changes you make to Push
2’s encoders as part of the clip. When you’re done recording parameter changes, press the
Automation button again to turn it off. To delete the changes you’ve recorded for a particular
parameter, press and hold the Delete button and touch the corresponding encoder. If automation
hasn’t been recorded for a parameter, holding Delete and touching an encoder will reset the
corresponding parameter to its default value.

Automated parameters are shown with a white dot next to the parameter in the display. Parameters
that you have overridden (by manually adjusting the parameter while not recording) will show a gray
dot.

Automated and/or Overridden Parameters are Indicated in the Display.

To re-enable all automation that you have manually overridden press and hold Shift and press the
Automation button.

33.13 Step Sequencing Automation

In both the drum and melodic step sequencers, it’s possible to automate parameters for the selected
step.

The parameters that are available will change depending on the display mode you are currently in.

When in Clip Mode, hold one or more steps to access note-specific parameters.

When in Device Mode or Mix Mode, hold one or more steps in order to create and edit device or
mixer automation for only the selected step(s). While holding a step and tweaking an encoder, the
corresponding parameter’s automation value will be adjusted specifically for the time represented by

that step. Note that per-step automation can be created for any step, even if that step doesn’t contain
notes.

33.14 Clip Mode

Press the Clip button to enter Clip Mode, where you can adjust various parameters for the selected
clip.

Clip Button.

When working with an audio track, if no clip is selected, Push will prompt you to load a sample.

Loading a Sample into an Empty Clip Slot in an Audio Track.

The display colors reflect the color of the clip, and the clip’s name is highlighted in the upper-left
corner. Some of the adjustable parameters change depending on the type of clip selected.

In MIDI tracks containing Drum Racks, notes are displayed in their respective pad color. In all MIDI
tracks, the velocity of each note is indicated by its opacity.

Clip Mode With a MIDI Clip Selected.

When a clip is playing on the selected track, the display follows the clip’s song position and scrolls
automatically.

For both MIDI and audio clips, the second upper display button toggles Loop on or off. With Loop on,
you can set the Loop Position, which is where within the clip the loop will begin. Loop Length sets how
many bars and/or beats long the loop is, as measured from the loop position. Start Offset allows you
to begin playback at a different point within the loop, rather than at the loop’s start position. If the
Loop Position and Start Offset are at the same position, moving the Loop Position will result in the Start
Offset moving along with it. With Loop off, you can control the Start and End position. This is the
region that will play (once) when the clip is launched.

Hold Shift while adjusting any of these controls to adjust by 16th-note subdivisions.

You can Zoom in or out of the sample with the first encoder. The position you’ll zoom to is centered
around the last position encoder you touched, e.g., Start, Length, Loop.

Clip Mode With an Audio Clip Selected.

When working with an audio clip, you can also set the clip’s Warp Mode, gain, and transposition.
Hold Shift while adjusting Transpose to adjust in cents rather than in whole semitones. Note that this
also adjusts the Detune parameter in Live’s Clip View.

33.14.1 Using MIDI Tracks in Clip Mode

When working with MIDI tracks in Clip Mode, you can view and refine played or sequenced MIDI
from Push 2.

The display will change depending on the currently selected pad layout.

In addition to the Zoom, Start, End, and Loop controls available in Clip Mode, all pad layouts provide
an additional Crop control, which lets you delete material that falls outside the selected loop.

33.14.2 Real-Time Playing Layouts

When recording your real-time playing using the 64 Notes, 64 Pads or 64 Slices layouts, Clip
Mode’s display lets you see the incoming MIDI notes, and the view adjusts so that all existing notes fit
on the display at the same time. Note that this “folded” display is also shown in Session Mode.

Clip Mode’s Folded Display.

33.14.3 Sequencing Layouts

In the melodic and drum step sequencer layouts, a semi-transparent white box on the display
indicates the sequenceable area. This represents the area on the pads where you can add, delete or
adjust notes.

Clip Mode’s Sequenceable Area.

Each sequenceable area corresponds to one page of steps. A box on the far left side of the display
indicates which pitch range the sequenceable area is in.

As notes are added, lines will appear on the far left side of the display. These lines indicate which
pitch ranges contain notes. You can use these indicator lines to find and edit notes quickly, without
looking at your computer screen.

Pitch ranges with a higher density of notes are represented by thicker lines.

Pitch Range and Note Indicators in Clip Mode.

33.14.3.1 Melodic Sequencer

The Melodic Sequencer layout has a range of eight notes on each page. The sequenceable area can
be moved horizontally via the loop length pads or Page Left/Right buttons, or vertically via the
Octave Up/Down buttons or touch strip.

33.14.3.2 Melodic Sequencer + 32 Notes

In this layout, the display will adjust to fit all notes in the clip. When a note(s) that exist in the clip is
selected, their sequenceable area will be highlighted on the display. This makes it quicker to locate
and edit steps containing the selected note(s). The sequenceable area can be moved horizontally via
the Page Left/Right buttons or the loop length pads, which can be accessed momentarily in the fifth
row by holding the Layout button.

Loop Length Pads in the Melodic Sequencer + 32 Notes Layout.

Drums/Slicing Loop Selector and 16 Velocities

The Loop Selector and 16 Velocities layouts show the selected pad only. The sequenceable area can
be moved horizontally via the loop length pads or Page Left/Right buttons, or vertically by selecting a
different pad.

33.14.4 Note-Specific Parameters

When working in any sequencing layout in Clip Mode, you can adjust note settings for each step. To
access these settings, simply press and hold a step. The display will zoom to the page containing that
step, and switch the controls to the step’s note settings. Notes contained within the selected step will
be highlighted.

Hold a Step to Zoom its Page and Access Clip Mode’s Note Parameters.

You can then adjust the corresponding encoders in order to:

•

•
•
•

Nudge notes backwards or forwards in time. The value represents the percentage that the note
is offset from the previous grid line. Negative values indicate that the note occurs before the
grid line.
Adjust the coarse Length of the selected notes.
Fine tune the length adjustment of the selected notes.
Change the Velocity of the selected notes.

You can also adjust these note-specific parameters for multiple steps at the same time. To do this, press
and hold all of the pads you’d like to adjust, and then tweak the encoders. The display will show the
range of values for the selected steps.

You can also create notes with your desired Nudge, Length, and Velocity values by holding an empty
step and then tweaking any of these encoders.

When working with drums, you can adjust nudge, length, and velocity for every note played by a
particular pad by pressing and holding the Select button, pressing the pad, and then adjusting the
encoders.

33.15 Controlling Live’s Session View

Press Push 2’s Session button to switch from Note Mode to Session Mode. You can press and hold the
Session button to temporarily toggle Session Mode. Releasing the button will then return to Note
Mode. Likewise, pressing and holding Note while in Session Mode will temporarily toggle Note
Mode.

Session Button.

In Session Mode, the 8x8 pad grid will now launch clips and the Scene/Grid Buttons will launch
scenes. Pressing a pad triggers the clip in the corresponding location in Live’s Session View. If the track
is selected, pressing the button records a new clip.

The pads light up in different colors so you know what’s going on:

•
•
•

The color of all playing or stopped clips is reflected on the pads.
Playing clips pulse in their color.
Recording clips pulse between red and the clip’s color.

Clip colors can be changed when in Session Mode. To do this, hold Shift and press a pad that
contains a clip. Then tap one of the pads on the outer ring to choose that color for the selected clip.

Pressing the Mute or Solo buttons will mute or solo the currently selected track, respectively. Hold
Mute or Solo and press any track’s lower display button to mute or solo that track. Holding the Mute
or Solo button for a few moments will lock it on. You can then release the button and toggle tracks on
and off just by pressing the corresponding lower display buttons. Press Mute or Solo again to unlock
it.

Pressing the Stop Clip button will stop the playing clip in the currently selected track. Hold Stop Clip
and press any track’s lower display button to stop the playing clip in that track.

Mute, Solo, and Stop Clip Buttons.

Holding the Stop Clip button for a few moments will lock it on. You can then release Stop Clip and
stop clips just by pressing the lower display button for the track you would like to stop. While Stop
Clip is locked on, the lower display buttons will pulse for any tracks that contain a currently playing
clip. Press Stop Clip again to unlock it.

To stop all clips, press and hold Shift, and then press Stop Clip.

Push 2 tells you what’s going on in the software, but, importantly, the software also reflects what’s
happening on the hardware. The clip slots currently being controlled by Push 2’s pad grid are shown
in Live with a colored border.

Hold the Duplicate button and press a clip to copy it. Continue holding Duplicate and tap another clip
slot to paste the clip there.

The arrows and Shift button increase the scope of the eight-by-eight grid.

•

•

Pressing the up or down arrows moves you up or down one scene at a time. Pressing the
Octave Up or Down buttons moves eight scenes up or down.
The left and right arrow keys move you left or right one track at a time. The Page left and right
buttons move eight tracks at a time.

While working in Session Mode when the focus is on Clip Mode, the display is “folded”, which means
all notes within a clip will fit on the display at any given time. Being able to see all notes within a clip
allows you to quickly identify it before launching it. To select a clip without launching it, press and hold
the Select button while tapping the pad containing that clip.

While recording MIDI from an external source (such as a MIDI sequencer or MIDI keyboard), the
folded display lets you see all incoming notes.

When in Session Mode, holding the Layout button gives you momentary access to the Session
Overview, which is explained in more detail below.

33.15.1 Session Overview

Push 2’s Session Overview lets you navigate through large Live Sets quickly without looking at your
computer screen.

Holding the Layout button gives you momentary access to Session Overview, where the pad grid
zooms out to reveal an overview of your Session View. You can also lock the Session Overview in
place by holding Shift and pressing the Layout button. To unlock the Session Overview, press the
Layout button again.

In the Session Overview, each pad represents an eight-scene-by-eight-track block of clips, giving you
a matrix of 64 scenes by 64 tracks. Hit a pad to focus on that section of the Session View. For
example, pressing the pad in row three, column one will put the focus on scenes 17-24 and tracks
1-8. Furthermore, each scene launch button represents a block of 64 scenes (if they are available in
your Set.)

In the Session Overview, the color coding is a little different:

•

•

•

White: indicates the currently selected block of clips, which will be surrounded by the colored
border in the software.
Green: there are clips playing in that block of clips (though that may not be the block of clips
selected).
No color: there are no tracks or scenes in that range.

33.16 Setup Menu

Press the Setup button to adjust brightness, the sensitivity of Push 2’s velocity response, and other
settings.

Setup Button.

Setup Options.

When Pad Sensitivity is turned up, it takes less force to trigger a higher velocity. A Pad Sensitivity of 10
results in higher output levels at any given input velocity, while a setting of 0 results in lower output
levels at the same velocity. The default (and recommended) setting is 5.

Pad Gain boosts or cuts the overall velocity curve. Higher values shift the curve towards the top of the
velocity range, while lower values reduce it. This control has a stronger effect at medium velocities. The
default (and recommended) setting is 5.

Pad Dynamics adjusts the spread of velocities across the output range. At a setting of 10, most
velocities will result in high or low output, without much in the middle. At 0, most velocities will result in
medium output levels (assuming Pad Gain is set to 5). The default (and recommended) setting is 5.

The easiest way to understand the relationship of the three velocity controls is by observing the
changes in the graphical curve below them. The striking force (input) is shown on the horizontal axis,
while the output level is shown on the vertical axis.

To use a linear velocity curve, set Pad Gain to 4 and Pad Dynamics to 7.

Display Light adjusts the brightness of Push 2’s display, while LED Brightness adjusts the brightness of
the pads and buttons. At very low LED Brightness settings, pads may appear to be the wrong color.
The default (and recommended) setting for both controls is 100%.

The Workflow option determines how Push 2 behaves when the Duplicate, New, or Up/Down arrow
buttons are pressed. Which mode you choose depends on how you like to organize your musical
ideas. In Scene Workflow (which is the default), musical ideas are organized and navigated in
scenes. In Clip Workflow, you’re working with only the currently selected clip.

In Scene Workflow:

•

•

•

Duplicate creates a new scene containing all of the currently playing clips, and seamlessly
switches to playing them back. This is the same as the Capture and Insert Scene command in
Live’s Create menu.
New is identical to Duplicate, except that it does not duplicate the currently selected clip.
Instead, an empty clip slot is prepared, allowing you to create a new idea in the current track.
The up and down arrows move up or down by a single scene. Playback of the clips in the new
scene begins seamlessly.

In Clip Workflow:

•

•

•

Duplicate creates a copy of the currently selected clip in the next clip slot, while continuing
playback of any currently playing clips in other tracks. Hold Shift while pressing Duplicate to
create a new scene containing all of the currently playing clips.
New prepares an empty clip slot on the currently selected track. Clips in other tracks are not
affected.
The up and down arrows move up or down by a single scene. Playback of the currently
selected track’s clip in the new scene begins seamlessly. Clips in other tracks are not affected.

33.17 Push 2 Control Reference

The function of each button and control is explained below.

Tap Tempo — As you press once every beat, the tempo of the Live Set will follow your tapping. If the
“Start Playback with Tap Tempo” button is enabled in Live’s Record, Warp & Launch Settings, you can
also use tapping to count in: If you are working in a 4/4 signature, it takes four taps to start song
playback at the tapped tempo. The encoder above the button adjusts Live’s tempo in increments of
one BPM. Holding Shift while adjusting will set the tempo in increments of .1 BPM.

Metronome — Toggles Live’s metronome on or off. The right encoder sets the amount of swing applied
when Quantizing, Record Quantizing or when Repeat is pressed.

Delete — In Note Mode, this button deletes the selected clip. When working with a Drum Rack, hold
Delete and press a pad to delete that pad’s notes in the clip (or the pad itself if there are no recorded
notes). In Session Mode, hold Delete and then press a clip to delete that clip. Hold Delete and select
a device or track with the upper and lower display buttons to delete the device or track. Hold Delete
and touch an encoder to delete automation controlled by that encoder. If automation has not been
recorded for a particular parameter, holding Delete and touching the corresponding encoder will
reset that parameter to its default value. In Simpler’s Slicing Mode, hold Delete and tap a pad to
delete that slice. If the Arrangement View is in focus in Live, pressing Delete will delete the currently
selected clip in the Arrangement.

Undo — Undoes the last action. Press and hold Shift while pressing Undo to Redo. Note that Push 2’s
Undo button applies Live’s Undo functionality, so it will undo actions in your Live Set even if they were
done without using Push 2.

Mute — Mutes the currently selected track. Hold Mute while pressing another track’s lower display
button to mute that track. Hold Mute while pressing a Drum Rack pad to mute the pad. Hold Mute
while pressing a step sequencer step to deactivate the step. Hold Mute while pressing a device’s
upper display button to deactivate the device. Holding the Mute button for a few moments will lock it
on. You can then release Mute and toggle devices or tracks on and off just by pressing the
corresponding upper or lower display buttons. Press Mute again to unlock it.

Solo — Solos the currently selected track. Hold Solo while pressing another track’s lower display
button to solo that track. Hold Solo while pressing a Drum Rack pad to solo the pad. Holding the Solo
button for a few moments will lock it on. You can then release Solo and toggle a track’s solo on and
off just by pressing the corresponding lower display button. Press Solo again to unlock it.

Stop Clip — Stops the playing clip in the currently selected track. Hold Stop Clip and press any track’s
lower display button to stop the playing clip in that track. While Stop Clip is held down, the lower
display buttons will pulse for any tracks that contain a currently playing clip. Press Stop Clip again to
unlock it. Hold Shift and press Stop Clip to stop all clips.

Convert — Converts the current instrument or clip into a different format. The details of the conversion
depend on what is selected when you press Convert:

•

•

•

•

While working with a Simpler in either Classic or One-Shot Mode, pressing Convert will create
a new MIDI track containing a Drum Rack, with a copy of the Simpler on the first pad. All other
devices that were in the original track will also be copied to the new track.
While working with a Simpler in Slicing Mode, pressing Convert will replace the Simpler on the
same track with a Drum Rack that contains all of the slices mapped to individual pads.
While working with a Drum Rack, pressing Convert will create a new MIDI track containing all
of the devices that were on the selected pad.
While working with an audio clip, pressing Convert allows you to choose between:

◦

◦

Creating a new MIDI track containing a Simpler or a new MIDI track containing a Drum
Rack, with the sample loaded to a Simpler on the first pad. Warp Markers and related
settings will be preserved in the new Simpler, as will all other devices that were in the
original track.
Converting a Harmony, Melody, or Drums to a new MIDI track.

Double Loop — Doubles the material within the loop, as well as the length of the loop.

Quantize — Press and release to quantize the selected notes (or all notes in the clip if there is no
selection). Hold Quantize and press a drum pad to quantize that pad’s notes. For audio clips,
Quantize will affect transients. Press and hold Quantize to access quantization settings. After
changing these settings, press once to exit and then press and release to apply your changes.

Duplicate — In Scene Workflow, Duplicate creates a new scene containing all of the currently playing
clips. In Clip Workflow, Duplicate creates a copy of the currently selected clip in the next clip slot,
while continuing playback of any currently playing clips in other tracks. Hold Duplicate while pressing
a Drum Rack pad to copy the pad and paste it to a new location in the Drum Rack. Hold Duplicate
while pressing a track selection button to duplicate that track. In Session Mode, hold Duplicate and
press a clip to copy it. Continue holding Duplicate and tap another clip slot to paste the clip there.

New — Pressing New stops the selected clip and prepares Live to record new material. This allows
you to practice before making a new recording.

Fixed Length — When enabled, all newly created clips will be a fixed number of bars. When
disabled, new clips will continue to record until you press the Record, New or Play/Stop buttons.
Press and hold, then use the lower display buttons to specify the fixed recording length. Enabling
Fixed Length while recording will switch recording off and loop the last few bars of the clip,
depending on the Fixed Length setting.

Automate — Toggles Live’s Automation Record button. When on, your parameter changes will be
recorded into playing Session View clips. Hold Shift and press Automate to re-enable any automation
that you have overridden. Hold Delete and press the Automation button to delete all automation in a
clip.

Record — With the Session View focused in Live, press the Record button to begin recording a Session
clip. Pressing Record again will stop recording but will continue playing back the clip. Pressing Record
a third time will enable overdub mode, allowing you to record into the clip while it plays back. Hold
Record and press the lower display button for a track to manually arm it. With the Arrangement View
focused in Live, pressing Record will toggle Arrangement Recording on and off. You can also trigger
Arrangement Recording while Live’s Session View is in focus by holding Shift and pressing Record.
Note that this behavior is reversed when the Arrangement is in focus; holding Shift and pressing
Record will then toggle Session recording.

Play/Stop — Toggles the play button in Live’s transport bar. While already stopped, hold Shift and
press Play/Stop to return Live’s transport to 1.1.1 without starting playback.

Touch Strip — When an instrument track is selected, the touch strip adjusts pitch bend or modulation
wheel amount when playing in real-time, or the available range of notes when step sequencing. Pitch
bend is selected by default when an instrument track is selected. To change the functionality of the
touch strip, hold Select and tap the strip. This toggles between pitch bend and mod wheel functionality
each time you tap it. The display will briefly show the current mode each time you change it. Note that
pitch bend and modulation wheel functionality is only available when playing instruments in real time,
and not when using the Melodic Sequencer. When a Drum Rack track is selected, the touch strip
selects the Drum Rack bank.

Encoders and display buttons — The encoders and the two banks of eight buttons above and below
the display change function depending on a variety of factors, including the selected track type, the
current mode, etc. In all modes, the far-right encoder controls the volume of the Main track or the Pre-
Cue volume if Shift is held. Holding Shift while adjusting any of the encoders allows you to fine-tune
whichever parameter is currently being controlled by that encoder.

Add Device — Opens Browse Mode to add a new device to the currently selected track. Devices will
load to the right of the previously-selected device, although note that MIDI effects will always be
placed before the instrument in the track and audio effects will always be placed after it.

Add Track — Puts Push 2 into Browse Mode, allowing you to select which type of track you’d like to
add (MIDI, Audio, or Return) and optionally load a device to the new track at the same time. If the
Add Track button is pressed while a track within a Group Track is selected, any new tracks will be
inserted into that Group Track.

Master — Press the Master button to select the Main track. Press Master again to return to the
previously selected track.

Scene/Grid buttons — These buttons change their functionality depending on whether Session Mode
or Note Mode is selected. When Session Mode is selected, these buttons launch Session View scenes.
Hold the Select button while pressing a Scene button to select the scene without launching it. When
Note Mode is selected, the Scene/Grid buttons determine the rhythmic resolution of the step
sequencer grid and the rhythmic resolution of repeated notes when Repeat is enabled.

Setup — Press to adjust brightness, the sensitivity of Push 2’s velocity response, and other settings.

User — All of Push 2’s built-in functionality can be disabled via User Mode. This allows Push 2 to be
reprogrammed to control alternate functions in Live or other software. Push 2’s relative encoders work
best in “Relative (2’s Comp.)” mode. To ensure this mode is selected, turn the encoder slowly to the left
during mapping.

Device — Press to enter Device Mode, which allows you to use the encoders and upper display
buttons to control parameters in Live’s devices and third-party plug-ins. While in another mode, press
and hold to temporarily toggle to Device Mode. Releasing the button will then return to the previous
mode.

Browse — Press to enter Browse Mode, where you can load instruments and effects to tracks.

Mix — Each press of the Mix button toggles between Track Mix Mode and Global Mix Mode. In
Track Mix Mode, the encoders adjust volume, pan, and send levels for the currently selected track.
The lower display buttons are used to select the track. While in another mode, press and hold to
temporarily toggle to Mix Mode. Releasing the button will then return to the previous mode.

Clip — Press to enter Clip Mode, where you can adjust parameters for the selected clip. While in
another mode, press and hold to temporarily toggle to Clip Mode. Releasing the button will then
return to the previous mode.

Arrow Keys — Navigate through your Live Set (in Session Mode) and between tracks or scenes/clips
(in Note Mode). In Browse Mode, use the arrows to move between columns of items in the browser.

Repeat — When Repeat is enabled, holding down a pad will retrigger the note. The Scene/Grid
buttons change the rhythmic value of the repeated note. Press and hold Repeat to temporarily enable
it.

Accent — When Accent is enabled, all incoming notes (whether step sequenced or played in real-
time) are played at full velocity. Press and hold Accent to temporarily enable it.

Scale — When Note Mode is on and an instrument track is selected, pressing this button allows you to
select which scale will be played on the pads. Note that this button has no effect when a Drum Rack
track is selected or when in Session Mode.

•

•

•

Fixed On/Off: When Fixed Mode is on, the notes on the pad grid remain in the same positions
when you change keys; the bottom-left pad will always play C, except in keys that don’t
contain a C, in which case the bottom-left pad will play the nearest note in the key. When Fixed
is off, the notes on the pad grid shift so that the bottom-left pad always plays the root of the
selected key.
In Key/Chromatic: With In Key selected, the pad grid is effectively “folded” so that only notes
within the key are available. In Chromatic Mode, the pad grid contains all notes. Notes that are
in the key are lit, while notes that are not in the key are unlit.
Scale selection: Using the upper and lower display buttons, you can change the key played by
the pad grid. You can change to a variety of scale types using encoders 2 through 7.

Layout — Press to change the layout of the pad grid. When in Session Mode, Layout toggles the
Session Overview on or off. When in Note Mode, the layout options depend on the type of track that
is currently selected and the current mode.

•

•

MIDI track containing an instrument — Toggles between enabling the pad grid for real-time
playing of notes and melodic step sequencing.
MIDI track containing a Drum Rack (or a Simpler in Slicing Mode) — Toggles between the
three-section pad grid (real-time playing, step sequencing, and loop length), and the 64-pad
layout.

Note — Press to enter Note Mode. When enabled, the pads change functionality based on the type
of track that is currently selected. While in Session Mode, press and hold Note to temporarily toggle
to Note Mode. Releasing the button will then return to Session mode.

•

•

MIDI track containing an instrument — The pads plays notes or slices of a sample when using
Simpler in Slicing Mode. Pressing Layout toggles between real-time playing and step
sequencing.
MIDI track containing a Drum Rack — With the Loop Selector layout selected, the pad grid is
divided; the lower-left 16 pads play the Drum Rack, the lower-right 16 pads adjust the loop
length of the clip, and the upper four rows control the step sequencer. Press Layout to switch to
16 Velocities layout. Here, the bottom right 16 pads represent 16 different velocities for the
selected Drum Rack pad. Press Layout again to switch to the 64-pad layout, allowing you to
play drums across the entire 8x8 pad grid.

Session — Press to enter Session Mode. When enabled, the pad grid changes to launch clips in Live’s
Session View. While in Note Mode, press and hold Session to temporarily toggle to Session Mode.
Releasing the button will then return to Note Mode.

Octave Up/Down — If an instrument track is selected, these buttons shift the pads up or down by
octave. If a Drum Rack is selected, these buttons shift the Drum Rack’s pad overview up or down by
16 pads. In Session Mode, these buttons shift control of the Session View up or down by eight scenes.
These buttons will be unlit if no additional octaves are available.

Page Left/Right — When working with the drum or melodic step sequencers, these buttons navigate to
the previous or next page of steps. In Session Mode, these buttons shift control of the Session View left
or right by eight tracks.

Shift — Press and hold Shift while pressing other buttons to access additional functionality. Hold Shift
while turning encoders for finer resolution.

Select — In Session Mode, hold Select and press a clip to select the clip without launching it. This will
also display the clip name in the display. In Note Mode, hold Select and press a Drum Rack pad to
select it without triggering the pad.

33.17.0.1 Using Footswitches with Push 2

Two ports on the back of Push 2 allow you to connect momentary footswitches. Footswitch 1 acts as a
sustain pedal. Footswitch 2 gives you hands-free control of Push 2’s recording functionality. A single
tap of the footswitch will toggle the Record button, thus switching between recording/overdubbing
and playback of the current clip. Quickly double-tapping the footswitch is the same as pressing the
New button.

Note that certain footswitches may behave “backwards”; for example, notes may sustain only when
the pedal is not depressed. Footswitch polarity can usually be corrected by connecting the footswitch
to the port while depressing it, but we recommend using footswitches with a physical polarity switch.

34. Synchronizing with Link, Tempo
Follower, and MIDI

34.1 Synchronizing via Link

Ableton Link is a technology that keeps devices in time over a wired or wireless network. Link is built
into Live as well as a growing number of iOS applications, and any Link-enabled software can play in
time with any other Link-enabled software simply by joining the same network.

When using Link, you can start and stop playback of each device or application independently of
every other connected device or application. Link-enabled software will remain in tempo as well as at
the correct position in relation to the global launch quantization of all participants.

34.1.1 Setting up Link

To configure Live to use Link, first make sure that your computer is connected to the same network as
any other devices that you will use Link with. This can either be a local network or an ad-hoc
(computer-to-computer) connection. Then open Live’s Link, Tempo & MIDI Settings and enable the
button next to “Show Link Toggle.”

Showing the Link Toggle in Live’s Settings.

It is possible to sync start and stop commands across all connected apps that have Start Stop Sync
enabled. To do this, click the button next to “Start Stop Sync”.

The Start Stop Sync Toggle in Live’s Settings.

34.1.2 Using Link

The Link toggle in Live’s Control Bar will appear. Click to toggle Link on or off.

Link Toggle.

When on, the toggle will update to show the number of other Link-enabled apps or instances of Live
that are on the same network.

Link Indicator Showing Another Connection.

If at least one other Link-enabled app or instance of Live is connected, the Arrangement Position
display will show a moving “progress bar” whenever Live’s transport is not running. This bar is a
representation of the Live Set’s global launch quantization in relation to that of the other participants in
the Link session. After you trigger playback, Live will wait until this bar is filled before starting.

Arrangement Position Shows Relation to Link Timeline.

The first app or Live instance to join a Link session will set the initial tempo for the others. Any Link-
enabled apps or instances of Live can then change their tempo at any time and all others will follow. If
multiple participants try to change the tempo simultaneously, everyone else will try to follow, but the
last one who changes the tempo will “win.”

Tempo changes made by any participant in a Link session will override tempo automation in your Live
Set.

Note that the metronome’s recording count-in cannot be used when Link is enabled.

In most cases, Link will work without issues as soon as it is enabled and will provide reliable
synchronization under all conditions. If you have further questions or run into issues, we recommend
checking out the Link FAQ in the Knowledge Base.

34.2 Synchronizing via Tempo Follower

You might encounter situations where a Link connection or MIDI Clock are not available. Or,
sometimes you might prefer not to use a rigid, computer-generated clock. For example, you might like
Live’s tempo to follow the natural push and pull of a drummer in your band, or you might be trying to
synchronize to a set of turntables during a DJ performance. This is where Tempo Follower comes in.
Tempo Follower analyzes an incoming audio signal in real-time and interprets its tempo, allowing Live
to follow along and keep in time.

34.2.1 Setting Up Tempo Follower

To set an external audio input as a source for Tempo Follower, first open Live’s Link, Tempo & MIDI
Settings. In the Tempo Follower section, set the Input Channel (Ext. In) to the input on your audio
interface that is connected to the source you wish to follow. For a drum kit, this might be a dedicated
overhead microphone. For turntables, you might choose to use a record output or effects loop from a
DJ mixer. Note that while Tempo Follower’s algorithm is optimized for use with audio signals that have
a clear rhythm, you can also be creative and experiment with different sources.

Tempo Follower Settings in Live’s Settings.

When the “Show Tempo Follower Toggle” switch is set to “Show”, you will see a “Follow” button
appear in the Control Bar, alongside the other tempo-related parameters, at the left-hand side.

The Follow Button in the Control Bar.

Activating the “Follow” button will turn on Tempo Follower, and Live will begin listening to the
configured audio source and interpreting its tempo. Note that Tempo Follower does not run when the
Follow button is hidden.

When Tempo Follower cannot be connected to the audio input device channel specified in the
Settings, the feature is disabled and the Follow button will appear grayed out.

Note: Link, Tempo Follower, and External Sync are mutually exclusive; the Link and the External Sync
switches are disabled when Tempo Follower is enabled. Live can still send MIDI clock information to
external devices when Tempo Follower is enabled, but it cannot receive it.

34.3 Synchronizing via MIDI

If you’re working with devices that don’t support Link, you can synchronize via MIDI. The MIDI
protocol defines two ways to synchronize sequencers, both of which are supported by Live. Both
protocols work with the notion of a sync host, which delivers a sync signal that is tracked by the sync
device(s).

MIDI Clock: MIDI Clock works like a metronome ticking at a fast rate. The rate of the incoming ticks is
tempo-dependent: Changing the tempo at the sync host (e.g., a drum machine) will cause the device
to follow the change. The MIDI Clock protocol also provides messages that indicate the song position.
With respect to MIDI Clock, Live can act as both a MIDI sync host and device.

MIDI Timecode: MIDI Timecode is the MIDI version of the SMPTE protocol, the standard means of
synchronizing tape machines and computers in the audio and film industry. A MIDI Timecode
message specifies a time in seconds and frames (subdivisions of a second). Live will interpret a
Timecode message as a position in the Arrangement. Timecode messages carry no meter-related
information; when slaving Live to another sequencer using MIDI Timecode, you will have to adjust the
tempo manually. Tempo changes cannot be tracked. Detailed MIDI Timecode Settings are explained
later in this chapter. With respect to MIDI Timecode, Live can only act as a MIDI sync device, not a
host.

34.3.1 Synchronizing External MIDI Devices to Live

Live can send MIDI Clock messages to an external MIDI sequencer (or drum machine). After
connecting the sequencer to Live and setting it up to receive MIDI sync, turn the device on as a sync
destination in Live’s Link, Tempo & MIDI Settings.

Choosing a MIDI Device for Live.

The lower indicator LED next to the Control Bar’s EXT button will flash when Live is sending sync
messages to external sequencers.

34.3.2 Synchronizing Live to External MIDI Devices

Live can be synchronized via MIDI to an external sequencer. After connecting the sequencer to Live
and setting it up to send sync, use Live’s Link, Tempo & MIDI Settings to tell Live about the connection.

Setting up Live as a MIDI Device.

When an external sync source has been enabled, the EXT button appears in the Control Bar. You can
then activate external sync either by switching on this button or by using the External Sync command
in the Options menu. The upper indicator LED next to the EXT button will flash if Live receives useable
sync messages.

The External Sync Switch.

When Live is synced to an external MIDI device, it can accept song position pointers from this device,
syncing it not only in terms of tempo but in terms of its position in the song. If the host jumps to a new
position within the song, Live will do the same. However, if the Control Bar’s Loop switch is activated,
playback will be looped, and song position pointers will simply be “wrapped“ into the length of the
loop.

When Link is enabled, Live can send MIDI clock information to external devices, but cannot receive it;
the External Sync switch is disabled when Link is enabled.

34.3.2.1 MIDI Timecode Options

Timecode options can be set up per MIDI device. Select a MIDI device from the Link, Tempo & MIDI
Settings’ MIDI Ports list to access the settings.

The MIDI Timecode Frame Rate setting is relevant only if “MIDI Timecode“ is chosen from the MIDI
Sync Type menu. The MIDI Timecode Rate chooser selects the type of Timecode to which Live will
synchronize. All of the usual SMPTE frame rates are available. When the Rate is set to “SMPTE All,“
Live will auto-detect the Timecode format of incoming sync messages and interpret the messages
accordingly. Note that you can adjust the Timecode format that is used for display in the Arrangement
View: Go to the Options menu, and then access the Time Ruler Format sub-menu.

The MIDI Timecode Offset setting is also only relevant if “MIDI Timecode“ is chosen from the Sync
Type menu. You can specify a SMPTE time offset using this control. Live will interpret this value as the
Arrangement’s start time.

34.3.3 Sync Delay

The Sync Delay controls, which are separately available for each MIDI device, allow you to delay
Live’s internal time base against the sync signal. This can be useful in compensating for delays incurred
by the signal transmission. The Sync Delay for a specific MIDI device appears as you select the MIDI
device from the Link, Tempo & MIDI Settings’ MIDI Ports list. To adjust the delay, have both Live and
the other sequencer play a rhythmical pattern with pronounced percussive sounds. While listening to
the output from both, adjust the Sync Delay control until both sounds are in perfect sync.

Adjusting Sync Delay.

35. Computer Audio Resources and
Strategies

Real-time audio processing can be a demanding task for general-purpose computers, which are
usually designed to run spreadsheets and surf the Internet. An application like Live requires a powerful
CPU and a fast SSD. This chapter will provide some insight on how you can avoid and solve computer
resource issues when using Live.

35.1 Managing the CPU Load

To output a continuous stream of sound through the audio hardware, Live has to perform a huge
number of calculations every second. If the processor can’t keep up with what needs to be calculated,
the audio will have gaps or clicks.

Factors that affect computational speed include processor clock rates (e.g., speed in MHz or GHz),
architecture, temperature (in hot environments, modern CPUs will “thermal throttle” and slow down the
CPU processing rate), memory cache performance (how efficiently a processor can grab data from
memory), and system bus bandwidth — the computer’s “pipeline“ through which all data must pass.

Fortunately, Live supports multicore and multiprocessor systems, allowing the processing load from
things like instruments, effects, and I/O to be distributed among the available resources. Depending
on the machine and the Live Set, the available processing power can be several times that of older
systems.

35.1.1 The CPU Load Meter

The Control Bar’s CPU meter displays how much of the computer’s computational potential is currently
being used. For example, if the displayed percentage is 10 percent, the computer is just coasting
along. If the percentage is 100 percent, the processing is being maxed out — it’s likely that you will
hear gaps, clicks or other audio problems.

Note that the CPU meter takes into account only the load from processing audio, not other tasks the
computer performs (e.g., managing Live’s user interface).

The CPU Load Meter.

The CPU meter can display the Average or Current CPU usage, or it can be switched off entirely.

The Average CPU meter displays the average percentage of the CPU currently processing audio,
rather than the overall CPU load. The Current CPU meter displays the total current CPU usage.

You can click on the CPU meter to display the various options.

The CPU Load Meter Options.

By default, Live will not display the Current level; it must be enabled from the drop-down menu.

In new installations of Live 11, the CPU Overload Indicator will also be switched off by default. This
option can be re-enabled from the drop-down menu as needed by selecting Warn on Current CPU
Overload.

To determine the CPU load, Live calculates the time it needs to process one audio buffer. This value is
then compared to the time it takes to actually play one audio buffer.

For example, a value of 50% on the CPU meter means that Live is processing one audio buffer twice
as fast as it takes to play the buffer.

Values over 100% are possible when the calculation takes more time than it does to play one audio
buffer.

Live expects that the audio thread will have the highest priority, however the final prioritization of
threads is done by the operating system, meaning Live’s processing might get interrupted. This is why
other applications may cause CPU spikes in Live’s CPU meter.

35.1.2 CPU Load from Multichannel Audio

One source of constant CPU drain is the process of moving data to and from the audio hardware. This
drain can be minimized by disabling any inputs and outputs that are not required in a project. There
are two buttons in the Audio Settings to access the Input and Output Configuration dialogs, which
allow activating or deactivating individual ins and outs.

Live does not automatically disable unused channels, because the audio hardware drivers usually
produce an audible “hiccup“ when there is a request for an audio configuration change.

35.1.3 CPU Load from Tracks and Devices

Generally, every track and device being used in Live incurs some amount of CPU load. However, Live
is “smart“ and avoids wasting CPU cycles on tracks and devices that do not contribute anything
useful.

For example, dragging devices into a Live Set that is not running does not significantly increase the
CPU load. The load increases only as you start playing clips or feed audio into the effects. When there
is no incoming audio, the effects are deactivated until they are needed again. If the effect produces a
“tail,“ like reverbs and delays, deactivation occurs only after all calculations are complete.

While this scheme is very effective at reducing the average CPU load of a Live Set, it cannot reduce
the peak load. To make sure your Live Set plays back continuously, even under the most intense
conditions, play back a clip in every track simultaneously, with all devices enabled.

In the Session View, it is possible to see each track’s impact on the CPU load by clicking on the Show/
Hide Performance Impact selector in the Mixer Section.

The Show/Hide Performance Impact selector.

In the Performance Impact section, each track has its own CPU meter with six rectangles that light up
to indicate the relative impact of that track on the CPU level of the current Set. Freezing the track with
the largest impact or removing devices from that track will usually reduce the CPU load.

The Session View’s Performance Impact Section.

35.1.4 Track Freeze

Live‘s Freeze Track command can greatly help in managing the CPU load incurred by devices and
clip settings. When you select a track and execute the Freeze Track command, Live will create a
sample file for each Session clip in the track, plus one for the Arrangement. Thereafter, clips in the
track will simply play back their “freeze files“ rather than repeatedly calculating processor-intensive
device and clip settings in real time. The Freeze Track command is available from Live‘s Edit menu and
from the context menu of tracks and clips. Be aware that it is not possible to freeze a Group Track; you
can only freeze tracks that hold clips.

Normally, freezing happens very quickly. But if you freeze a track that contains an External Audio
Effect or External Instrument that routes to a hardware effects device or synthesizer, the freezing
process happens in real-time. Live will automatically detect if real-time freezing is necessary, and
you‘ll be presented with several options for managing the process. Please see the section on real-time
rendering for an explanation of these options.

Once any processing demands have been addressed (or you have upgraded your machine!), you
can always select a frozen track and choose Unfreeze Track from the Edit menu to change device or
clip settings. On slower machines, you can unfreeze processor-intensive tracks one at a time to make
edits, freezing them again when you are done.

Many editing functions remain available to tracks that are frozen. Launching clips can still be done
freely, and mixer controls such as volume, pan, and the sends are still available. Other possibilities
include:

•
•
•
•
•
•

Edit, cut, copy, paste, duplicate, and trim clips.
Draw and edit mixer automation and mixer clip envelopes.
Consolidate clips.
Record Session View clip launches into the Arrangement View.
Create, move, and duplicate Session View scenes.
Drag frozen MIDI clips into audio tracks.

When performing edits on frozen tracks that contain time-based effects such as reverb, you should
note that the audible result may be different once the track is again unfrozen, depending on the
situation. This is because, if a track is frozen, the applied effects are not being calculated at all, and
therefore cannot change their response to reflect edited input material. When the track is again
unfrozen, all effects will be recalculated in real time.

A Frozen Arrangement Track with a Reverb Tail.

Frozen Arrangement View tracks will play back any relevant material extending beyond the lengths of
their clips (e.g., the “tails“ of Reverb effects). These frozen tails will appear in the Arrangement as
crosshatched regions located adjacent to their corresponding clips. They are treated by Live as
separate, “temporary“ clips that disappear when unfrozen, since the effect is then calculated in real
time. Therefore, when moving a frozen clip in the Arrangement, you will usually want to select the
second, frozen tail clip as well, so that the two remain together.

For frozen Session clips, only two loop cycles are included in the frozen clip, which means that clips
with unlinked clip envelopes may play back differently after two loop cycles when frozen.

Dragging a frozen clip to the drop area in the Session View or Arrangement View will create a new
frozen track containing that clip. If a clip is partially selected in the Arrangement, the new frozen track
will contain the selected portion of the clip only.

The samples generated by the Freeze Track command are stored in the Current Project folder under /
Samples/Processed/Freeze. If the Set has not yet been saved, the folder location will be specified by
the Temporary Folder. Please note that freeze files for tracks that contain an External Instrument or
External Audio Effect will be discarded immediately when unfreezing.

You can also decide to flatten frozen tracks, which completely replaces the original clips and devices
with their audible result. The Flatten command is available from the Edit menu.

Besides providing an opportunity to conserve CPU resources on tracks containing a large number of
devices, the Track Freeze command simplifies sharing projects between computers. Computers that
are a bit low on processing power can be used to run large Live Sets as long as any CPU-intensive
tracks are frozen. This also means that computers lacking certain devices used in one Live Set can still
play the Set when the relevant device tracks are frozen.

35.2 Managing the Disk Load

An SSD’s read/write speed can affect Live’s performance. The amount of disk traffic Live generates is
roughly proportional to the number of audio channels being read or written simultaneously. For
example, a track playing a stereo sample causes more disk traffic than a track playing a mono
sample.

The Disk Overload Indicator.

The Disk Overload indicator flashes when the disk was unable to read or write audio quickly enough.
When recording audio, this condition causes a gap in the recorded sample; when playing back, you
will hear dropouts.

Do the following to avoid disk overload:

•

•
•

Reduce the number of audio channels being written by choosing mono inputs instead of stereo
inputs in the Audio Settings’ Channel Configuration dialog.
Use RAM Mode for selected clips.
Reduce the number of audio channels playing by using mono samples instead of stereo
samples when possible. You can convert stereo samples to mono using any standard digital
audio editing program, which can be called up from within Live.

36. Audio Fact Sheet

Much of Ableton‘s development effort has been focused on carefully and objectively testing Live‘s
fundamental audio performance. As a result of this testing, we have regularly implemented a number
of low-level improvements to the audio engine. We have written this fact sheet to help users
understand exactly how their audio is (or is not) being modified when using certain features in Live
that are often misunderstood, as well as tips for achieving the highest quality results.

The focus of our research has been on objective (that is, quantifiable and measurable) behavior. We
make no claims about what you can hear because we cannot possibly predict the variables that make
up your listening environment, audio hardware, hearing sensitivity, etc. Furthermore, this research
makes no claims about how Live compares to other audio software. Rather, it is a summary of
measurable facts about what Live actually does under various conditions.

36.1 Testing and Methodology

As of this writing, every version of Live is subjected to a number of automated tests that cover every
aspect of Live‘s functionality. We add additional tests as we add features, and we will never release
an update unless it passes every test.

36.2 Neutral Operations

Procedures in Live that will cause absolutely no change in audio quality are referred to as neutral
operations. You can be sure that using these functions will never cause any signal degradation.
Applying neutral operations to audio that was recorded into Live ensures that the audio will be
unchanged from the point of analog-to-digital conversion. Applying neutral operations to files
imported into Live ensures that the imported audio will be identical to the files saved on disk. Applying
neutral operations to files being exported from Live ensures that the quality of your output file will be
at least as high as what you heard during playback.

The list of neutral operations found below is provided primarily as an abstract reference; while all of
these operations are, in fact, neutral, it is important to remember that each of them may (and almost
certainly will) occur within a context that also contains non-neutral operations. For example, running
an audio signal through an effects device is a non-neutral operation. So any neutral operations that

occur after it will, of course, still result in audio that is altered in some way. Even a gain change is,
technically, non-neutral.

Neutral operations include:

36.2.1 Undithered Rendering

The Export Audio/Video command renders Live’s audio output to a file on disk. Rendering is a neutral
operation under certain conditions:

•

•

The sample rate of the rendered file is the same as that set for the audio hardware in Live‘s
Settings.
No non-neutral operations have been applied.

Live‘s rendering performance is tested by loading three types of unprocessed audio files (white noise,
fixed-frequency sine waves and sine sweeps) in 16-, 24- and 32-bit word lengths and rendering
these to output files, also with varying bit resolutions. Phase cancellation testing of the original and
output files shows the following:

•

•

•

Rendering to a file with the same bit depth as the original results in complete phase
cancellation.
Rendering to a file with a higher bit depth than the original results in complete phase
cancellation.
Rendering to a file with a lower bit depth than the original results in the smallest amount of
distortion possible within a 32-bit system.

36.2.2 Matching sample rate/no transposition

Playback of an unstretched audio file in Live is a neutral operation, provided that the file‘s sample rate
is the same as that set in Live‘s Settings and that the file is played back without transposition. This is
verified by cancellation tests of rendered output. Please note that “playback“ in this context refers only
to the audio within Live, prior to the point at which it reaches your audio hardware.

36.2.3 Unstretched Beats/Tones/Texture/Re-Pitch Warping

If the tempo of a clip is the same as the tempo of the Set, that clip will play back unstretched. In this
case, if the Warp mode of the clip is set to Beats, Tones, Texture, or Re-Pitch (but not Complex or
Complex Pro), playback will be neutral.

Any Warping caused by changing the Set’s tempo is non-permanent, and audio that plays back
unwarped at a given tempo will always play back unwarped at that tempo, even if the tempo is
changed and then changed back. For example, if you’ve recorded some tracks at 120 BPM, but then
decide you’d like to slow the tempo down to record a particularly difficult solo passage, the original

tracks will play back neutrally again after returning the tempo to 120 BPM. Only the recording made
at the slower tempo will be stretched.

Recording tempo automation in the Arrangement can play back neutrally or not depending on the
Warp Mode. When using Beats mode with transient preservation on, artifacts may occur. These can
be eliminated by preserving 16ths instead of transients, or by using the Repitch Warp Mode.

Please note that grooves work by modifying the positions of Warp Markers. This means that playback
of audio clips with groove applied will be non-neutral even at the original tempo.

The neutrality of unstretched clip playback is verified by performing cancellation tests on rendered
output.

36.2.4 Summing at Single Mix Points

Live uses double precision (64-bit) summing at all points where signals are mixed, including clip and
return track inputs, the Main track and Racks. Mixing in Live is thus a neutral operation for signals
mixed at any single summing point. This is tested by loading pairs of 24-bit files (white noise and
fixed-frequency sine waves and their phase-inverted complements), adding the pairs together eight
times and rendering the output as 32-bit files. All tests result in perfect phase cancellation.

Please note that, while 64-bit summing is applied to each single mix point, Live‘s internal processing is
still done at 32-bit. Thus, signals that are mixed across multiple summing points may still result in an
extremely small amount of signal degradation. This combination of 64-bit summing within a 32-bit
architecture strikes an ideal balance between audio quality and CPU/memory consumption.

36.2.5 Recording external signals (bit depth >/= A/D converter)

Recording audio signals into Live is a neutral operation, provided that the bit depth set in Live‘s
Settings window is the same or higher than that of the A/D converters used for the recording. In this
context, “neutral“ means “identical to the audio as it was delivered to Live by the A/D converters.“

36.2.6 Recording internal sources at 32 bit

Audio that is recorded via internal routing will be identical to the source audio, provided that the
recording was made at 32 bits. To ensure neutral recordings of plug-in instruments and any audio
signals that are being processed by effects plug-ins, internal recording at 32 bits is recommended.
Please note, however, that if the source audio is already at a lower bit depth, internal recording at that
bit depth will also be neutral (assuming that no effects are used); internally recording an unprocessed
16 bit audio file at 32 bits will not increase the sound quality.

The neutrality of internal recording is verified using cancellation tests.

36.2.7 Freeze, Flatten

When tracks are frozen, the audio files that are created are 32 bit, which ensures that they will not be
lower quality than the audio heard prior to freezing. But there are some special cases involving Freeze
that result in non-neutral behavior and should be noted:

Frozen Arrangement View tracks can include audio material that extends beyond the end of the clip
itself, such as reverb tails and delay repetitions. Frozen Session View tracks, however, are always
exactly two loop cycles long, so any audio that extends beyond two loop cycles during unfrozen
playback will be cut off after freezing.

Time-based effects like reverbs and delays are processed in real-time for unfrozen clips, so stopping
playback during a reverb or delay tail will allow the tail to continue. In contrast, frozen tails are
rendered as audio, and so will stop abruptly during playback.

Any parameter automations are rendered as part of the audio file for frozen Arrangement View clips.
Frozen Session View clips, however, take a “snapshot“ of all parameter values at the Arrangement‘s
1.1.1 position and retain them for the duration of the frozen clip. This is analogous to the behavior with
unfrozen clips; when playing normal clips in Session View, any Arrangement automations are
“punched out“ until the Back to Arrangement button is pressed.

Frozen clips are always played back with Warp on and in Beats mode, which means they are subject
to the same non-neutral behavior as any other warped audio files.

Any devices with random parameters (e.g., the Chance control in the Beat Repeat device) will no
longer exhibit random behavior after freezing. This is because, as with time-based effects, the random
values that were in place at the moment of freezing will be rendered as part of the new file, and will
thus no longer be calculated in real-time.

Please note that the Flatten command replaces any original clips and devices with the audio files
created by freezing. When using this command, it is important to keep in mind the special cases
above — what you hear after freezing is exactly what you will get when flattening, so if the results are
not to your liking, be sure to unfreeze and make any necessary changes to device parameters before
invoking the Flatten command.

This procedure is tested by rendering the output of an audio track and comparing it to the frozen
audio from the same track via phase cancellation to ensure that the files are identical.

36.2.8 Bypassed Effects

Bypassed effects in Live are removed from the signal flow. This is true for both Live‘s built-in effects
devices and third-party VST and AU plug-ins. Consequently, audio at the output of a bypassed effect
is identical to the audio at the input. Please note, however, that effects devices with parameters that
inherently require delay (e.g., the Lookahead settings in Compressor) will still introduce this delay
when bypassed, in order to maintain automatic delay compensation with the rest of the project. In
most cases, the effects of this behavior will be completely inaudible.

The neutrality of bypassed effects is tested by loading one instance of each of Live‘s effects devices
into an audio track, deactivating them, and then rendering the output of the track. The rendered file is
then compared to the rendered output of the same track with no loaded devices. Phase cancellation
testing of the two files confirms that they are identical.

36.2.9 Routing

The routing of signals within Live is a neutral operation. The signal at the routing destination will be
identical to the signal at the routing source. It is important to note that Live‘s flexible routing
architecture allows for a variety of scenarios, including routing from before or after any track‘s effects
or mixer and tapping the output of individual sample slots within the Impulse instrument. In these
cases, it is likely that the signal heard at the output point will be different from the signal heard prior to
routing, because it has been tapped before reaching the end of its original signal chain.

36.2.10 Splitting Clips

Clips which are already neutral will remain neutral after splitting. Splitting only affects playback
position within the sample, and has no effect on the sample data itself. Playback across a split
boundary is seamless and sample-accurate.

The neutrality of clip splitting is tested under a variety of conditions:

•
•

Splitting unwarped clips with loop on and off.
Splitting warped but unstretched clips with loop on and off.

In all cases, output is rendered and compared with the output of an unsplit version of the same source.
Phase cancellation testing of the two files confirms that they are identical.

36.3 Non-Neutral Operations

Procedures in Live that will cause a change in audio quality are referred to as non-neutral operations.
Users can be guaranteed that using these operations will cause at least some change to the signal.
Applying non-neutral operations to files imported into Live ensures that the imported audio will differ
from the files saved on disk. Applying non-neutral operations to files being exported from Live ensures
that what you hear during real-time playback will be different from what will end up in your new file.

Non-neutral operations are outlined below.

36.3.1 Playback in Complex and Complex Pro Mode

The algorithms used in the Complex and Complex Pro Warp Modes use an entirely different
technology from the algorithms behind Beats, Tones, Texture, and Re-Pitch modes. Although the
Complex modes may sound better, particularly when used with mixed sound files containing different
kinds of audio material, they are never neutral — not even at the original tempo. Because of this, and
because of the increased CPU demands of these algorithms, we recommend using them only in cases
where the other Warp Modes don‘t produce sufficient results.

36.3.2 Sample rate conversion/transposition

Sample rate conversion (during both real-time playback and rendering) is a non-neutral operation.
Playback of audio files at a sample rate that is different from the rate set in Live‘s Settings window will
cause signal degradation. Transposition is also a form of sample-rate conversion, and thus also results
in non-neutral behavior.

To minimize potential negative results during real-time playback, it is recommended to do sample rate
conversion as an offline process, rather than mixing files of different sample rates within a single Set.
Once the samples have been exported at the sample rate that you plan to use in Live, the files can be
imported without any loss of quality.

Rendering audio from Live with a sampling rate other than the one that was used while working on the
project is also a non-neutral operation. Sample rate conversion during export uses the extremely high-
quality SoX Resampler library, as licensed under the GNU LGPL v2.1, which results in downsampled
files with extremely low distortion.

36.3.3 Volume Automation

Automation of volume level results in a change in gain, which is necessarily a non-neutral operation.
But certain implementations of automation envelopes can result in audible artifacts, particularly if the
envelopes are not calculated at a fast enough rate. Volume automation curves are updated for each
audio sample, resulting in extremely low levels of distortion.

36.3.4 Dithering

Whenever rendering audio to a lower bit depth, it is a good idea to apply dithering in order to
minimize artifacts. Dithering (a kind of very low-level noise) is inherently a non-neutral procedure, but
it is a necessary evil when lowering the bit resolution.

Please note that Live‘s internal signal processing is all 32-bit, so applying even a single gain change
makes the resulting audio 32-bit as well — even if the original audio is 16- or 24-bit. Dither should
never be applied more than once to any given audio file, so unless you are mastering and finalizing
in Live, it is best to always render at 32-bit and avoid dithering altogether.

36.3.5 Recording external signals (bit depth < A/D converter)

Recording audio signals into Live is a non-neutral operation if the bit depth set in Live‘s Settings
window is lower than that of the A/D converters used for the recording. This is not recommended.

36.3.6 Recording internal sources below 32 bit

Audio that is recorded via internal routing will lose quality if the recording is made at a bit depth
below 32 bits. To ensure neutral recordings of plug-in instruments and any audio signals that are
being processed by effects plug-ins, internal recording at 32 bits is recommended. Please note,
however, that if the source audio is already at a lower bit depth, internal recording at that bit depth
will also be neutral (assuming that no effects are used); internally recording an unprocessed 16 bit
audio file at 32 bits will not increase the sound quality.

36.3.7 Consolidate

Consolidating clips in the Arrangement View creates new audio files, which are non-neutral in
comparison to the original audio data. Specifically, the new files will be normalized, with their clip
volumes adjusted to play back at the same volume as heard prior to consolidation. Normalization is a
gain change, which is a non-neutral operation. Also, the new files will be created at the sample rate
and bit depth set in Live‘s Settings window, which may differ from those in the original audio files.

36.3.8 Clip Fades

When Create Fades on Clip Edges is enabled in the Record, Warp & Launch Settings, a short (up to 4
ms) fade is applied to the clip start and end to avoid clicks at the clip edges. These “declicking“ fades
can also be applied to Session View clips via the Clip Fade button. Additionally, Arrangement View
clips have editable fades and crossfades. Applying any of these fade options is a non-neutral
operation.

36.3.9 Panning

Live uses constant power panning with sinusoidal gain curves. Output is 0 dB at the center position
and signals panned fully left or right will be increased by +3 dB. In order to minimize this volume
change, it may be helpful to narrow the overall stereo width before doing extreme panning. This can
be done via the Width control in the Utility device.

36.3.10 Grooves

Under most conditions, playback of a warped clip that is at the same tempo as the Set is a neutral
operation. However, if a groove is applied, playback will be non-neutral at any tempo.

36.4 Tips for Achieving Optimal Sound Quality

in Live

For users looking to achieve optimal audio quality in Live, we have provided a list of recommended
practices and program settings.

•

•

•

•
•
•

Decide which sample rate to use for a project prior to beginning work, rather than changing the
sample rate while working on the project.
Record audio into Live using high-quality hardware components (audio interface, cables, etc.)
and at the highest sample rate and bit depth your interface and computer will support.
Avoid using samples that are at different sample rates within the same project. If you want to
work with such files, we recommend that you first convert them to the sample rate set for your
audio interface in an offline application that is optimized for this task.
For all audio clips, disable both the Warp and Fade options in the Clip View.
Do not adjust the Transpose and Detune controls for any clips.
Always render at 32-bit.

Please note that these practices, while ensuring optimal audio quality, disable some of Live‘s
functionality — in particular, stretching and synchronization.

36.5 Conclusion

We hope this helps users to understand exactly how audio is affected when performing various
procedures in Live. Our focus has been on functions that have proven over the years to cause
confusion or uncertainty, and the list of both neutral and non-neutral operations presented here is
necessarily incomplete.

37. MIDI Fact Sheet

In conjunction with our work on the audio engine, Ableton has spent additional effort analyzing Live‘s
MIDI timing and making improvements where necessary. We wrote this fact sheet to help users
understand the problems involved in creating a reliable and accurate computer-based MIDI
environment, and to explain Live‘s approach to solving these problems.

The MIDI timing issues discussed in this chapter are generally not applicable to users with high-quality
audio and MIDI hardware. If you have already invested time and money into optimizing these factors
in your studio, and are not experiencing problems with MIDI timing, you probably do not need this
information.

37.1 Ideal MIDI Behavior

To understand how MIDI works within a digital audio workstation (DAW), it is helpful to introduce
some common terms and concepts. A DAW must be able to accommodate three distinct MIDI-related
scenarios:

1.

2.

3.

Recording refers to sending MIDI note and controller information from a hardware device (such
as a MIDI keyboard) into a DAW for storage. An ideal recording environment would capture
this incoming information with perfect timing accuracy in relation to the timeline of the song —
as accurately as an audio recording.
Playback refers to two related scenarios when dealing with DAWs. The first involves sending
MIDI note and controller information from the DAW to a hardware device such as a
synthesizer. The second involves converting stored MIDI information into audio data within the
computer, as played back by a plug-in device such as the Operator synthesizer. In both cases,
an ideal playback environment would output a perfect reproduction of the stored information.
Playthrough involves sending MIDI note and controller information from a hardware device
(such as a MIDI keyboard) into the DAW and then, in real-time, back out to a hardware
synthesizer or to a plug-in device within the DAW. An ideal playthrough environment would
“feel“ as accurate and responsive as a physical instrument such as a piano.

37.2 MIDI Timing Problems

The realities of computer-based MIDI are complex, and involve so many variables that the ideal
systems described above are impossible to achieve. There are two fundamental issues:

1.

2.

Latency refers to inherent and consistent delay in a system. This is a particular problem in a
DAW because digital audio cannot be transferred into or out of an audio interface in real time,
and must instead be buffered. But even acoustic instruments exhibit a certain degree of latency;
in a piano, for example, there is some amount of delay between the time a key is depressed
and the time the hammer mechanism actually activates the string. From a performance
perspective, small latency times are generally not a problem because players are usually able
to adapt the timing of their playing to compensate for delays — as long as the delays remain
consistent.
Jitter refers to inconsistent or random delay in a system. Within a DAW, this can be a particular
problem because different functions within the system (e.g., MIDI, audio and the user interface)
are processed separately. Information often needs to be moved from one such process to
another — when converting MIDI data into a plug-in‘s playback, for example. Jitter-free MIDI
timing involves accurate conversion between different clocks within the system‘s components —
the MIDI interface, audio interface, and the DAW itself. The accuracy of this conversion
depends on a variety of factors, including the operating system and driver architecture used.
Jitter, much more so than latency, creates the feeling that MIDI timing is “sloppy“ or “loose.“

37.3 Live’s MIDI Solutions

Ableton‘s approach to MIDI timing is based on two key assumptions:

1.

2.

In all cases, latency is preferable to jitter. Because latency is consistent and predictable, it can
be dealt with much more easily by both computers and people.
If you are using playthrough while recording, you will want to record what you hear — even if,
because of latency, this occurs slightly later than what you play.

Live addresses the problems inherent in recording, playback and playthrough so that MIDI timing will
be responsive, accurate and consistently reliable. In order to record incoming events to the correct
positions in the timeline of a Live Set, Live needs to know exactly when those events were received
from the MIDI keyboard. But Live cannot receive them directly — they must first be processed by the
MIDI interface‘s drivers and the operating system. To solve this problem, the interface drivers give
each MIDI event a timestamp as they receive it, and those are passed to Live along with the event so
that Live knows exactly when the events should be added to the clip.

During playthrough, a DAW must constantly deal with events that should be heard as soon as
possible, but which inevitably occurred in the past due to inherent latency and system delays. So a
choice must be made: should events be played at the moment they are received (which can result in

jitter if that moment happens to occur when the system is busy) or should they be delayed (which adds
latency)? Ableton‘s choice is to add latency, as we believe that it is easier for users to adjust to
consistent latency than to random jitter.

When monitoring is enabled during recording, Live adds an additional delay to the timestamp of the
event based on the buffer size of your audio hardware. This added latency makes it possible to record
events to the clip at the time you hear them — not the time you play them.

For playback of hardware devices, Live also generates timestamps that it attempts to communicate to
the MIDI interface drivers for scheduling of outgoing MIDI events. Windows MME drivers cannot
process timestamps, however, and for devices that use these drivers, Live schedules outgoing events
internally.

Even during high system loads that cause audio dropouts, Live will continue to receive incoming MIDI
events. In the event of audio dropouts, there may be timing errors and audio distortion during
playthrough, but Live should still correctly record MIDI events into clips. Later, when the system has
recovered from the dropouts, playback of these recorded events should be accurate.

37.4 Variables Outside of Live’s Control

In general, timestamps are an extremely reliable mechanism for dealing with MIDI event timing. But
timestamps are only applicable to data within the computer itself. MIDI data outside of the computer
can make no use of this information, and so timing information coming from or going to external
hardware is processed by the hardware as soon as it arrives, rather than according to a schedule.
Additionally, MIDI cables are serial, meaning they can only send one piece of information at a time.
In practice, this means that multiple notes played simultaneously cannot be transmitted simultaneously
through MIDI cables, but instead must be sent one after the other. Depending on the density of the
events, this can cause MIDI timing problems.

Another issue that can arise, particularly when working with hardware synthesizers from the early
days of MIDI, is that the scan time of the device may occur at a relatively slow rate. Scan time refers to
how often the synthesizer checks its own keyboard for input. If this rate is too slow, jitter may be
introduced.

Of course, any such timing problems present at the hardware level may be multiplied as additional
pieces of gear are added to the chain.

Even within the computer, the accuracy of timestamps can vary widely, depending on the quality of
the MIDI hardware, errors in driver programming, etc. Live must assume that any timestamps attached
to incoming MIDI events are accurate, and that outgoing events will be dealt with appropriately by
any external hardware. But both situations are impossible for Live to verify.

Tests and Results

Our procedure for testing the timing of incoming MIDI events is represented in the following diagram:

MIDI Input Test Configuration.

The output of a MIDI Source (a keyboard or other DAW playing long sequences of random MIDI
events) is fed to a zero-latency hardware MIDI Splitter. One portion of the splitter‘s output is recorded
into a new MIDI clip in Live. The other portion is fed to a MIDI-to-Audio Converter. This device
converts the electrical signal from the MIDI source into simple audio noise. Because the device does
not interpret the MIDI data, it performs this conversion with zero-latency. The converter‘s output is then
recorded into a new audio clip in Live. In an ideal system, each event in the MIDI clip would occur
simultaneously with the corresponding event in the audio clip. Thus the difference in timing between
the MIDI and audio events in the two clips can be measured to determine Live‘s accuracy.

In order to assess MIDI performance under a variety of conditions, we ran the tests with three different
audio/MIDI combo interfaces at different price points, all from well-known manufacturers. We will
refer to these interfaces as A, B and C. All tests were performed with a CPU load of approximately
50% on both macOS and Windows machines, at both 44.1 and 96 kHz and at three different audio
buffer sizes, for a total of 36 discrete test configurations.

Windows:

•

•

•

Interface A: The maximum jitter was +/- 4 ms, with the majority of the jitter occurring at +/- 1
ms.
Interface B: For most of the tests, the maximum jitter was +/- 3 or 4 ms. At 96 kHz and 1024
sample buffer, there were a small number of events with +/- 5 ms of jitter. At 44.1 kHz and 512
sample buffer, occasional events with +/- 6 ms occurred. In all cases, the majority of the jitter
occurred at +/- 1 ms.
Interface C: For most of the tests, the maximum jitter was +/- 5 ms. At 96 kHz and 512 sample
buffer, there were a small number of events with between +/- 6 and 8 ms of jitter. At 44.1 kHz
and 1024 sample buffer, there were a small number of events with jitter as high as +/- 10 ms.
In all cases, the majority of the jitter occurred at +/- 1 ms.

macOS:

•

•

•

Interface A: At 44.1 kHz and 1152 sample buffer, jitter was fairly evenly distributed between
+/- 4 and 11 ms. For all other tests, the maximum jitter was +/- 5 ms. In all tests, the majority of
the jitter occurred at +/- 1 ms.
Interface B: For most of the tests, the maximum jitter was +/- 4 or 5 ms. At 44.1 kHz and 1152
sample buffer, there was a fairly even distribution of jitter between +/- 2 and 11 ms. In all
cases, the majority of the jitter occurred at +/- 1 ms.
Interface C: In all tests, the maximum jitter was +/- 1 ms, with most events occurring with no
jitter.

We also performed a similar procedure for testing the timing of outgoing MIDI events, as represented
in the following diagram:

MIDI Output Test Configuration.

In all cases, the output tests showed comparable results to the input tests.

37.5 Tips for Achieving Optimal MIDI

Performance

In order to help users achieve optimal MIDI performance with Live, we have provided a list of
recommended practices and program settings.

•

•

•

Use the lowest possible buffer sizes available on your audio hardware, thereby keeping
latency to a minimum. Audio buffer controls are found in the Audio tab of Live‘s Settings, and
vary depending on the type of hardware you‘re using. For more information, see the Lesson
“Setting Up Audio I/O.“
Use a high quality MIDI interface with the most current drivers in order to ensure that MIDI
timestamps are generated and processed as accurately as possible.
Do not enable track monitoring if you are recording MIDI while listening directly to a hardware
device such as an external synthesizer (as opposed to listening to the device‘s audio through
Live via the External Instrument device). Likewise, disable track monitoring when recording MIDI
data that is generated by another MIDI device (such as a drum machine). When monitoring is
enabled, Live adds latency to compensate for playthrough jitter. Therefore, it is important to
only enable monitoring when actually playing through.

37.6 Summary and Conclusions

We hope this helps users understand a variety of related topics:

•

The inherent problems in computer-based MIDI systems.

•
•

Our approach to solving these problems in Live.
Additional variables that we cannot account for.

As mentioned before, the best way to solve MIDI timing issues in your studio is to use the highest-
quality hardware components available. For users of such components, all software MIDI systems
should perform with no noticeable issues. For users with less-than-optimal hardware, however, Live
still offers an additional degree of accuracy by minimizing jitter, but at the expense of a small amount
of additional latency.

38. Accessibility and Keyboard
Navigation

Live 12 offers new accessibility features on both macOS and Windows, including support for screen
readers and other assistive technologies that use the accessibility communication protocols native to
those operating systems. Additional improvements include a high-contrast option for new themes,
streamlined keyboard navigation, and a more organized Settings menu.

While most of Live’s views, controls, and devices work with screen readers, some device features have
not been optimized to do so, such as the Modulation Matrix in Wavetable and some advanced
parameters in Operator. Several other Live and third-party features are not yet supported for screen
reader use, including:

•
•
•
•

Browser tagging and filters
MPE editing in Clip View
Max for Live
Some third-party plug-ins

For answers to common questions about Live’s accessibility support, please refer to the Accessibility in
Ableton Live FAQ in the Knowledge Base.

38.1 Menu and Keyboard Navigation Settings

Various accessibility and keyboard navigation options can be found in Live’s Settings, as well as in the
Options and Navigate menus.

In addition to improved keyboard navigation, various keyboard shortcuts are available for common
actions and commands.

38.1.1 Using Tab for Navigation

When the Use Tab Key to Move Focus option is enabled via the Navigate menu or Live’s Display &
Input Settings, the Tab key can be used to navigate in the following ways:

•
•

Tab moves to the next control.
Shift

Tab moves to the previous control.

The Tab key can also be used to navigate between controls in the Session and Arrangement mixers
via these shortcuts:

•
•

Ctrl

Ctrl

Tab (Win) / Option
Shift

Tab (Win) / Option

Tab (Mac) moves to the next control in the same row.

Shift

Tab (Mac) moves to the previous control in

the same row.

When Use Tab Key to Move Focus is off, pressing the Tab key switches between Session and
Arrangement View, as in previous versions of Live.

In addition to using Tab to move focus, the following navigation options are also available:

•

•

Tab moves focus to the last control. This option can be enabled via

Wrap Tab Navigation - When this option is enabled, pressing Tab moves focus back to the
first control after reaching the last one in an area instead of stopping. If the first control is
selected, pressing Shift
the Navigate menu or the Display & Input Settings.
Move Clips with Arrow Keys - This option is enabled by default and lets you use the left and
right arrow keys to move selected clips and/or the time selection in Arrangement View. This
behavior can be switched off in the Display & Input Settings if needed. When off, pressing the
left arrow key collapses the time selection to the start point, while pressing the right arrow key
collapses the time selection to the end point.

38.1.2 Settings Menu

To open Live’s Settings, use the shortcut Ctrl

, (Win) / Cmd

, (Mac).

The Tab and Shift
These shortcuts work regardless of whether the Use Tab Key to Move Focus option is active or not.

Tab keys can be used to navigate between options inside the Settings tabs.

When a command is focused in any of the Settings tabs, the up and down arrow keys can be used to
change the state of a toggle, make value adjustments, or cycle through the available options for a
given command. It is also possible to use the Enter key to switch between toggle states.

To navigate between the different tabs in the Settings Page Chooser, use Ctrl
Shift
Option

Tab (Win) /
Tab (Mac) or the up
and down arrow keys when the chooser is focused. If the keyboard focus is on the first control of any
given Settings tab, use the Shift

Tab shortcut to return the focus to the Settings Page Chooser.

Tab (Mac) and Ctrl

Tab (Win) / Option

Shift

You can close the Settings window by using the Esc key.

Note that if you choose a new preferred language for the UI in the Display & Input Settings, Live must
be restarted for the change to take effect.

38.1.3 Options Menu

You can find further accessibility settings in Live’s Options menu, which contains an Accessibility sub-
menu. To access this sub-menu with the keyboard, use Alt
VoiceOver (Mac).

M then O with

O (Win) / VO

The sub-menu contains several entries for enabling certain screen reader announcements, such as
Speak Menu Commands, Speak Minimum and Maximum Slider Values, and Speak Time in Seconds.

38.1.4 Speak Help Text

Most controls and areas in Live include descriptive text, accessible via the Info View. On Windows,
you can enable screen reader announcements for these descriptions by activating the Speak Help
Text option in your preferred screen reader. On macOS, you can do so by turning on help text in the
VoiceOver Utility’s verbosity settings. You can also access this option manually by pressing VO
Shift

H .

38.2 Audio Setup

To configure your audio settings in Live, open the Settings menu using the shortcut Ctrl
Cmd

, (Mac), then use the arrow keys to navigate to the Audio page.

, (Win) /

You can use Tab to move between the options on the Audio page and start configuring your audio
device settings.

Audio setup varies between macOS and Windows. On macOS, Live’s input and output can be
connected to any CoreAudio device. You can also select other drivers from the Driver Type drop-
down menu if needed. On Windows, you can select your preferred driver, for example ASIO4ALL,
and manage connected devices via the driver’s own program.

38.3 Connecting MIDI Devices

Live automatically detects connected MIDI devices, many of which require no further configuration.

Some MIDI controllers also come with control surface scripts to help integrate them into Live’s
workflows. Note that screen reader support for control surfaces varies between third-party
manufacturers, so some controllers may not be optimized for use with screen readers.

The MIDI section in the Link, Tempo & MIDI page has six Control Surface drop-down menus, where
you can select control surfaces using the dedicated keyboard navigation options. You can also
specify the input and output port settings for each selected control surface.

To learn more about MIDI configuration in Live, check out the MIDI and Key Remote Control chapter.

38.4 Navigating in Live

You can navigate through most of Live’s menus, views, and controls using the computer keyboard.
Note that the Use Tab Key to Move Focus option in the Navigate menu or Display & Input Settings
must be enabled if you want to use any of the Tab -based shortcuts mentioned in this section.

38.4.1 Navigate Menu

You can use the Navigate menu to access all of Live’s main views and other navigation options. Most
of the menu’s entries also come with corresponding keyboard shortcuts. To open the Navigate menu,
use Alt

M then N with VoiceOver (Mac).

N (Win) / VO

38.4.1.1 Control Bar - Alt

0 (Win) / Option

0 (Mac)

The Control Bar consists of various project settings, transport controls, mouse and keyboard tools, and
status views. The controls are organized into accessible groupings; you can use Tab and Shift
Tab to navigate between them with Speak Help Text activated to learn about each option.

The Control Bar remembers your last-focused control and focus returns to this control when you come
back to the Control Bar from another view.

38.4.1.2 Session View - Alt

1 (Win) / Option

1 (Mac)

The Session View is Live’s non-linear approach to music-making. There are four main sections in this
view:

Track Title Bars are displayed for all tracks in your Set. To navigate between track title bars, use the
left and right arrow keys. Right-clicking on a track title bar opens the context menu, which contains
useful track-related commands and their corresponding keyboard shortcuts.

Clip Slots are grouped by tracks (vertical from top to bottom) and scenes (horizontal from left to right).
Slots on audio tracks can contain audio clips, and slots on MIDI tracks can contain MIDI clips. When
focused on a clip slot in a MIDI track, you can insert an empty MIDI clip using Ctrl
(Win) / Cmd
M (Mac). You can launch a selected clip by pressing Enter . If Live’s
transport is running, the clip will begin playing based on the current setting in the Control Bar’s

Shift

Shift

M

quantization menu. Note that while clip slots also appear in return tracks, these slots cannot contain or
launch any clips.

Scenes can be used to trigger adjacent clips in different tracks at the same time via the Main track
scene numbers, which can be navigated between using the up and down arrow keys. Scenes can be
launched with the Enter key.

The Mixer contains routing and mixer options for each track. You can customize which mixer elements
are shown using the Mixer Controls sub-menu in the View menu or using the drop-down menu next to
the Mixer view control in the bottom right corner of Live’s window. These elements include input/
output assignment, send levels, volume controls, track options, crossfader controls, and performance
impact monitoring. The last three options are hidden by default.

You can navigate between track title bars, clip slots, and scenes using the arrow keys.

To jump from tracks/slots to the mixer, use Tab and Shift
a track’s mixer controls using Tab and Shift

Tab .

Tab . You can also navigate between

To move focus to the same control on a different track, you can use the Next Neighbor and Previous
Neighbor commands in the Navigate menu or the shortcuts Ctrl
(Mac) and Ctrl

Tab (Win) / Option

Tab (Win) / Option

Tab (Mac).

Shift

Shift

Tab

Use the Esc key to move focus from the currently focused element in a track to that track’s title bar.

38.4.1.3 Arrangement View - Alt

2 (Win) / Option

2 (Mac)

The Arrangement View is a timeline-style view for arranging audio, MIDI, and automation in Live.

There are a few different ways to navigate through the Arrangement View:

Navigating through Tracks

•
•

Move between tracks using the up and down arrow keys.
Move between track mixers using Ctrl
through a track’s mixer controls using Tab and Shift

Tab (Win) / Option
Tab .

Tab (Mac) and navigate

Navigating through the Timeline

•

•
•

Move forward or backward in time following the current grid settings using the left and right
arrow keys.
Widen or narrow the Arrangement View’s grid settings using the + and - keys.
Move to the previous/next clip edge or locator in a content lane using Ctrl (Win) /
Option (Mac) and the left and right arrow keys.

Using Locators

•

•

Add a locator by first navigating to the desired location on the timeline using the arrow keys.
Next, use Tab to focus the Set Locator button, then press Enter .
Navigate between locators using Tab and Shift

Tab .

•

Delete a locator by navigating to it and then press the Delete key.

Handling Content - Select content in the timeline by holding Shift and then using the arrow keys. -
Move selected content using the left and right arrow keys. - Cut selected content using Ctrl
(Win) / Cmd
Paste selected content using Ctrl
D (Win) / Cmd
Ctrl

D (Mac). - Delete selected content using the Delete key.

X (Mac). - Copy selected content using Ctrl

V (Mac). - Duplicate selected content using

C (Win) / Cmd

V (Win) / Cmd

C (Mac). -

X

Adjusting Clip Edges

•

Lengthen or shorten a clip by moving the insert marker to the clip’s edge, then pressing Enter
and using the left and right arrow keys to adjust the length. Press Enter again to confirm the
changes, or press Esc to cancel.

Exporting Audio

•

Select a region in the timeline and use the shortcut Ctrl
open the audio export dialog. By default, the Main track will be rendered.

R (Win) / Cmd

R (Mac) to

Note: Editing audio clip fades is not currently supported for screen reader use.

38.4.1.4 Clip View - Alt

3 (Win) / Option

3 (Mac)

The Clip View is where clip properties can be set and adjusted. You can double-click on any clip in
3 (Win) /
the Arrangement or Session View to open Clip View, or use the shortcut Ctrl
Cmd

Option

Alt

3 (Mac).

Clip View consists of two main areas: the clip panels and an editor.

The clip panels contain various options for adjusting note properties. Use the shortcut Alt
P (Mac) to bring focus to the panels from another view.
P (Win) / Option

Shift

Shift

Various editors are available for audio waveforms, MIDI notes, clip envelopes, and MPE data. When
a clip is opened in Clip View for the first time, the Sample Editor is displayed for audio clips, while the
MIDI Note Editor is displayed for MIDI clips. Use the shortcut Alt
3 (Mac)
to bring focus to the active editor from another view.

3 (Win) / Option

You can navigate in Clip View the following ways:

Working with the MIDI Note Editor

•

•

•
•

Enable MIDI Note Editor Preview in the Options menu to hear the notes when you add, select,
or move them in the editor.
Place the insert marker anywhere in the MIDI Note Editor, then hold Shift and use the left
and right arrow keys to select time.
Select any MIDI notes contained in a time selection using the Enter key.
Move the insert marker to the previous or next note boundary using Ctrl (Win) / Option
(Mac) and the left and right arrow keys.

Navigating through MIDI Notes

•

•

•

Jump to the previous or next note using Ctrl and the up and down arrow keys (Win) /
Option and the up and down arrow keys (Mac).
Jump to the previous or next note of the same pitch using Ctrl and the left and right arrow
keys (Win) / Option and the left and right arrow keys (Mac).
Add the Shift modifier to the above shortcuts to extend the note selection.

Editing MIDI Notes

•
•
•

•

•

•

Transpose selected notes using the up and down arrow keys.
Transpose selected notes by octaves using Shift and the up and down arrow keys.
Shorten or lengthen selected notes based on the current grid settings using Shift and the left
and right arrow keys.
Move selected notes in time based on the current grid settings using the left and right arrow
keys.
Adjust the velocity of selected notes using Ctrl (Win) / Cmd (Mac) and the up and down
arrow keys.
Adjust the probability of selected notes using Ctrl
the up and down arrow keys.

Alt (Win) / Cmd

Option (Mac) and

Working with Audio Clips

•
•

•
•

•

Move the insert marker using Ctrl (Win) / Option (Mac) and the left and right arrow keys.
Hold the Shift modifier to start a time selection, then use the left or right arrow key to extend
or shorten it.
Move a selected Warp Marker using the left and right arrow keys.
Insert and select a Warp Marker at the current position using Ctrl
(Mac).
Insert a transient at the current position using Ctrl
(Mac).

I (Win) / Cmd

I (Win) / Cmd

Shift

Shift

I

I

Note: MPE editing is not currently supported for use with screen readers.

38.4.1.5 Device View - Alt

4 (Win) / Option

4 (Mac)

The Device View displays the chain of devices loaded onto a track. MIDI tracks can contain MIDI
effects, instruments, and audio effects. Audio tracks, group tracks, return tracks, and the Main track
can contain audio effects.

Each device that is loaded onto a track is represented to screen readers as a group. You can move
between devices using the left and right arrow keys.

Devices can be cut, copied, pasted, duplicated, or deleted using the following keyboard shortcuts:

•
•
•

Cut: Ctrl
Copy: Ctrl
Paste: Ctrl

X (Win) / Cmd

X (Mac)

C (Win) / Cmd
V (Win) / Cmd

C (Mac)
V (Mac)

•
•

Duplicate: Ctrl
Delete: Delete

D (Win) / Cmd

D (Mac)

Navigate through a selected device’s controls using Tab and Shift

Tab .

Note: Most devices in Live offer basic accessibility support; however, more complex devices haven’t
yet been optimized for screen readers.

38.4.1.6 Browser - Alt

5 (Win) / Option

5 (Mac)

The browser contains your library of instruments, devices, and files. It is divided into four main sections:
the search bar, filters, sidebar, and content pane.

You can bring focus to the search bar from anywhere in Live using the shortcut Ctrl
Cmd

F (Mac). This also automatically selects the All label in the browser’s sidebar, which contains

F (Win) /

all browser content. Search results are displayed in the content pane.

Use the Tab key to switch between different areas of the browser. When the search bar is focused,
pressing Tab first moves focus to the Show/Hide Filter View toggle, then to the Filter View menu,
and finally to the sidebar. When the sidebar is focused, pressing Tab moves focus to the filters (if
shown) or to the content pane. You can also press the down arrow key to move focus from the search
bar to the content pane.

The sidebar contains various labels for different browser items, such as the included Core Library
content, Live Packs, Collections, and more. You can move between labels using the up and down
arrow keys. When a label is selected, its contents are displayed in the content pane. You can move
between the sidebar and content pane using the left and right arrow keys.

The content pane displays a list of devices and files based on selected browser label. You can multi-
select content using Shift and the up and down arrow keys. You can expand a selected folder
using the right arrow key, and collapse the folder using the left arrow key.

Some browser items, such as clips and instrument presets, include an audio preview. To hear the
preview when browsing, enable the Browser File Preview entry in the Options menu. Even if
previewing is switched off, you can still play the preview by pressing the right arrow key when a
browser item is selected.

Note: Filtering and tagging is not yet supported for use with screen readers.

38.4.1.7 Groove Pool - Alt
