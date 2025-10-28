Here is a detailed methodology document for implementing a natural language parser for complex, hierarchical commands.

-----

## **Methodology: Parsing Hierarchical DAW Commands**

### 1\. Overview

The goal is to translate a complex natural language (NL) command, such as "set return A reverb feedback to 20%", into a precise, executable instruction for the Ableton Live API.

This requires a multi-stage processing pipeline that moves from a general "intent" to a specific, resolved "target." The system cannot rely on simple keyword spotting. It must understand the **structure** of the user's Live set and the **relationships** between tracks, devices, and parameters.

The core of this methodology is to parse the user's command *against* an internal data model of the Live set.

### 2\. Prerequisite: The Live Set State Model

Before you can parse any commands, your application **must** maintain an internal, real-time representation of the Ableton Live set. This "State Model" is the data structure you will use to resolve ambiguity.

**Structure:**
This model should be a hierarchical object (like a tree or nested dictionaries/maps).

  * **Set (Root)**
      * `Tracks` (List)
          * **Track Object**
              * `Name`: "Return A"
              * `Aliases`: ["verb return", "rev A"]
              * `Devices` (List)
                  * **Device Object**
                      * `Name`: "Reverb"
                      * `Aliases`: ["verb"]
                      * `Parameters` (List or Map)
                          * **Parameter Object**
                              * `Name`: "Feedback"
                              * `Aliases`: []
                              * `API_Reference`: [Internal pointer to the actual API object]
                              * `Value_Type`: (e.g., Percent, dB, On/Off, Enum)
                          * **Parameter Object**
                              * `Name`: "Dry/Wet"
                              * `Aliases`: ["mix"]
                              * `...`
          * **Track Object**
              * `Name`: "Vocals"
              * `Devices`: [...]

**Population:**
This model must be populated by querying the Ableton Live API when the set is loaded or changed. You will need functions to fetch all tracks, then iterate over each track to fetch its devices, and then iterate over each device to fetch its parameters.

-----

### 3\. The Command Processing Pipeline

When a user issues a command, it passes through the following stages.

#### Stage 1: Intent Recognition

  * **Goal:** Determine the user's primary *action*.
  * **Methodology:**
    1.  Normalize the input string (lowercase, remove punctuation).
    2.  Check the string for primary "action" keywords. This can be a simple lookup.
    <!-- end list -->
      * `"set"`, `"change"`, `"adjust"` $\rightarrow$ **Intent: `set_parameter`**
      * `"mute"`, `"silence"` $\rightarrow$ **Intent: `set_mute`**
      * `"solo"` $\rightarrow$ **Intent: `set_solo`**
      * `"what is"`, `"read"`, `"get"` $\rightarrow$ **Intent: `get_parameter`**
  * **Output:** A single, clear `Intent` (e.g., `set_parameter`).

-----

#### Stage 2: Primary Entity Extraction (Slot Filling)

  * **Goal:** Isolate the main "chunks" of information required by the intent.
  * **Methodology:** For a `set_parameter` intent, you need two "slots": the **Target Path** and the **Value**.
    1.  Use a list of "delimiter" keywords (e.g., 'to', 'at', 'by') to split the string.
    2.  **Example:** `set return A reverb feedback to 20%`
          * **Intent:** `set` (from Stage 1)
          * **Delimiter:** `to`
          * **Resulting Chunks:**
              * **Target Path String:** "return A reverb feedback"
              * **Value String:** "20%"
  * **Output:** A `Target Path String` and a `Value String`.

-----

#### Stage 3: Hierarchical Path Resolution (The Core Algorithm)

  * **Goal:** Convert the `Target Path String` ("return A reverb feedback") into a *unique API reference* from your **State Model**.
  * **Methodology:** This is an iterative, top-down search.
    1.  **Tokenize:** Split the `Target Path String` into tokens: `['return', 'A', 'reverb', 'feedback']`.
    2.  **Initialize Search:** Start at the root of your **State Model** (the `Set` level).
    3.  **Step A: Match Track**
          * Iteratively combine tokens and search all `Track` names and aliases in the model.
          * Try: `"return"` $\rightarrow$ (Finds "Return A", "Return B"). **Ambiguous.**
          * Try: `"return A"` $\rightarrow$ (Finds one unique track: `Track: "Return A"`). **Match Found.**
          * *If a match is found, "consume" those tokens and narrow the search scope.*
    4.  **Step B: Match Device**
          * **Remaining Tokens:** `['reverb', 'feedback']`
          * **Search Scope:** *Only* the `Devices` list within the matched `Track: "Return A"`.
          * Try: `"reverb"` $\rightarrow$ (Finds one unique device: `Device: "Reverb"`). **Match Found.**
    5.  **Step C: Match Parameter**
          * **Remaining Tokens:** `['feedback']`
          * **Search Scope:** *Only* the `Parameters` list within the matched `Device: "Reverb"`.
          * Try: `"feedback"` $\rightarrow$ (Finds one unique parameter: `Parameter: "Feedback"`). **Match Found.**
  * **Output:** A specific, resolved `Parameter Object` from your State Model (which contains the direct API reference).

-----

#### Stage 4: Value Normalization

  * **Goal:** Convert the `Value String` ("20%") into a format the API understands (e.g., a float $0.2$).
  * **Methodology:** Use a set of rules based on the string content and (ideally) the `Value_Type` stored in the resolved `Parameter Object`.
      * `"20%"` $\rightarrow$ Remove '%', divide by 100 $\rightarrow$ $0.2$
      * `"0.5"` $\rightarrow$ Parse as float $\rightarrow$ $0.5$
      * `"half"` $\rightarrow$ $0.5$
      * `"on"` $\rightarrow$ $1.0$ (or `true`)
      * `"off"` $\rightarrow$ $0.0$ (or `false`)
      * `"-6 db"` $\rightarrow$ This is more complex. For a simple linear parameter ($0-127$), you might map this to a specific value. For a true dB parameter, you'd send the number $-6$.
  * **Output:** A normalized, API-ready `Value`.

-----

#### Stage 5: Execution & Ambiguity Handling

  * **Goal:** Execute the command or ask for clarification.

  * **Methodology:**

    **Scenario A: Success**

    1.  All stages succeeded. You have a `Parameter Object` and a normalized `Value`.
    2.  Use the `API_Reference` from the `Parameter Object` to call the Ableton Live API with the new `Value`.
    3.  Provide "success" feedback to the user ("OK, set feedback to 20%").

    **Scenario B: Ambiguity (Failure in Stage 3)**

    1.  **Command:** "set reverb feedback to 20%"
    2.  **Stage 3 Action:**
          * The parser tries to find a Track named "reverb" or "feedback" and fails.
          * It *must* then "skip a level" and search *all devices in the entire set* for "reverb".
          * **Result:** It finds `Device: "Reverb"` on `Track: "Return A"` AND `Device: "Reverb"` on `Track: "Vocals"`.
    3.  **The System's Response:**
          * **DO NOT GUESS.**
          * The system must stop and generate a clarifying question based on the multiple matches it found.
          * **Response:** "Which reverb did you mean? The one on 'Return A' or 'Vocals'?"

### 4\. Final Parsed Object

The entire pipeline's goal is to turn the raw string into a structured object like this, which you can then use to execute the command:

```
{
  "Original_String": "set return A reverb feedback to 20%",
  "Intent": "set_parameter",
  "Resolved_Target": [Pointer to Parameter Object for "Feedback"],
  "Resolved_Value": 0.2,
  "Status": "Success"
}
```

Or, in case of failure:

```
{
  "Original_String": "set reverb feedback to 20%",
  "Intent": "set_parameter",
  "Status": "Ambiguous",
  "Clarification_Question": "Which reverb did you mean?",
  "Options": [
    [Pointer to "Reverb" on "Return A"],
    [Pointer to "Reverb" on "Vocals"]
  ]
}
```