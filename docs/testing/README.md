# Testing Documentation Index

**Quick reference guide to all testing documentation**

---

## 📚 Available Test Documents

### 1. [FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md) - **START HERE**
**Purpose:** Overview of all new features and what's been changed
**Read this first if:** You want to understand what you're testing
**Time:** 10 minutes read
**Contains:**
- Feature descriptions with code locations
- API endpoint reference
- Integration map
- Testing strategy overview

---

### 2. [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md) - **QUICK START**
**Purpose:** Rapid smoke tests for critical functionality
**Use this for:** Daily verification, pre-commit checks, quick demos
**Time:** 5-10 minutes to complete
**Contains:**
- 17 quick tests (5 critical, 12 extended)
- Pass/fail checklist
- Debug commands
- Visual checks

**Run this:**
- ✅ Before committing UI changes
- ✅ After pulling new code
- ✅ Before demos
- ✅ Daily smoke tests

---

### 3. [WEB_UI_FEATURE_TEST_PLAN.md](./WEB_UI_FEATURE_TEST_PLAN.md) - **COMPREHENSIVE**
**Purpose:** Full test coverage for all new features
**Use this for:** Pre-release testing, QA cycles, bug investigation
**Time:** 30-45 minutes to complete
**Contains:**
- 10 test suites (90+ test cases)
- Detailed setup instructions
- Expected results for each test
- Browser console debugging
- Performance benchmarks
- Error handling scenarios

**Run this:**
- ✅ Before releases
- ✅ After major refactors
- ✅ When bugs are reported
- ✅ Monthly regression testing

---

### 4. [VISUAL_TESTING_GUIDE.md](./VISUAL_TESTING_GUIDE.md) - **REFERENCE**
**Purpose:** Visual expectations and UI validation
**Use this for:** Understanding what the UI should look like, screenshot guides
**Time:** Reference document (read as needed)
**Contains:**
- Before/after visual examples
- Layout expectations
- Color schemes
- Expected animations
- Common visual bugs
- Screenshot checklist

**Use this when:**
- ✅ Verifying UI changes
- ✅ Investigating layout issues
- ✅ Creating documentation screenshots
- ✅ Training new testers

---

### 5. [INTENTS_CHAT_INTEGRATION_TEST.md](./INTENTS_CHAT_INTEGRATION_TEST.md) - **REGRESSION**
**Purpose:** Test plan for intents-based chat routing (feature flag)
**Use this for:** Regression testing of core chat functionality
**Time:** 20 minutes to complete
**Contains:**
- 10 test cases for intent execution
- Feature flag toggle tests
- Fallback path verification
- Network debugging

**Run this:**
- ✅ When testing feature flag changes
- ✅ For regression on core chat functionality
- ✅ Before changing intent parsing logic

---

## 🎯 Testing Strategy by Scenario

### Scenario 1: "I just pulled new code, does it work?"
**Documents to use:**
1. [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md) - Tests #1-5 (Critical Path)

**Time:** 5 minutes

---

### Scenario 2: "I'm preparing for a release"
**Documents to use:**
1. [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md) - Full checklist
2. [WEB_UI_FEATURE_TEST_PLAN.md](./WEB_UI_FEATURE_TEST_PLAN.md) - All test suites
3. [INTENTS_CHAT_INTEGRATION_TEST.md](./INTENTS_CHAT_INTEGRATION_TEST.md) - Regression
4. [VISUAL_TESTING_GUIDE.md](./VISUAL_TESTING_GUIDE.md) - Visual verification

**Time:** 90 minutes

---

### Scenario 3: "UI looks weird, is this a bug?"
**Documents to use:**
1. [VISUAL_TESTING_GUIDE.md](./VISUAL_TESTING_GUIDE.md) - Check expected visuals
2. [WEB_UI_FEATURE_TEST_PLAN.md](./WEB_UI_FEATURE_TEST_PLAN.md) - Test Suite 4 (Compact Chat UI)

**Time:** 10 minutes

---

### Scenario 4: "Parameter accordion not working"
**Documents to use:**
1. [WEB_UI_FEATURE_TEST_PLAN.md](./WEB_UI_FEATURE_TEST_PLAN.md) - Test Suites 5, 6, 7
2. [FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md) - Feature #5, #6, #7 explanations

**Time:** 15 minutes

---

### Scenario 5: "Help responses seem wrong"
**Documents to use:**
1. [WEB_UI_FEATURE_TEST_PLAN.md](./WEB_UI_FEATURE_TEST_PLAN.md) - Test Suite 3 (Context-Aware Help)
2. [FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md) - Feature #3 details

**Time:** 10 minutes

---

### Scenario 6: "Performance is slow"
**Documents to use:**
1. [WEB_UI_FEATURE_TEST_PLAN.md](./WEB_UI_FEATURE_TEST_PLAN.md) - Test Suite 9 (Performance)
2. [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md) - Test #15 (Network Performance)

**Time:** 10 minutes

---

## 🛠️ Quick Reference: Test Commands

### Check Server Health
```bash
curl http://127.0.0.1:8722/health
```

### Check Config
```bash
curl http://127.0.0.1:8722/config | jq .features
```

### Test Snapshot API
```bash
curl http://127.0.0.1:8722/snapshot | jq .
```

### Test Capabilities API
```bash
curl "http://127.0.0.1:8722/return/device/capabilities?index=0&device=0" | jq .
```

### Toggle Feature Flag
```bash
# Disable
curl -X POST http://127.0.0.1:8722/config/update \
  -H 'Content-Type: application/json' \
  -d '{"features":{"use_intents_for_chat":false}}'

# Enable
curl -X POST http://127.0.0.1:8722/config/update \
  -H 'Content-Type: application/json' \
  -d '{"features":{"use_intents_for_chat":true}}'
```

### Browser Console: Check Feature Flags
```javascript
fetch('http://127.0.0.1:8722/config')
  .then(r => r.json())
  .then(c => console.log('Features:', c.features));
```

### Browser Console: Test Capabilities
```javascript
fetch('http://127.0.0.1:8722/return/device/capabilities?index=0&device=0')
  .then(r => r.json())
  .then(d => console.log('Capabilities:', d));
```

---

## 📋 Test Execution Tracking

### Daily Smoke Tests
**Frequency:** Daily (or before commits)
**Document:** [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md)
**Last Run:** _______________
**Status:** ☐ Pass ☐ Fail
**Notes:**

---

### Weekly Regression
**Frequency:** Weekly
**Document:** [INTENTS_CHAT_INTEGRATION_TEST.md](./INTENTS_CHAT_INTEGRATION_TEST.md)
**Last Run:** _______________
**Status:** ☐ Pass ☐ Fail
**Notes:**

---

### Pre-Release Full Test
**Frequency:** Before releases
**Documents:** All
**Last Run:** _______________
**Status:** ☐ Pass ☐ Fail
**Notes:**

---

## 🐛 Bug Reporting Template

When filing bugs, include:

**Summary:**
One-line description

**Document/Test:**
Which test document/suite revealed the bug

**Steps to Reproduce:**
1.
2.
3.

**Expected:**
What should happen (reference test doc)

**Actual:**
What actually happened

**Screenshots:**
(if applicable)

**Browser/Environment:**
- Browser:
- OS:
- Server version:
- Commit hash:

**Console Errors:**
```
Paste any errors here
```

**Network Requests:**
```
Paste relevant failed requests
```

---

## 📊 Test Coverage Matrix

| Feature | Quick Test | Full Test | Visual Test | Regression |
|---------|------------|-----------|-------------|------------|
| Device Capabilities API | ✅ #9 | ✅ Suite 1 | ✅ Sec 2 | - |
| Snapshot API | ✅ #8 | ✅ Suite 2 | - | - |
| Context-Aware Help | ✅ #4,#7 | ✅ Suite 3 | ✅ Sec 4,5 | - |
| Compact Chat UI | ✅ #5 | ✅ Suite 4 | ✅ Sec 1,7 | ✅ Test 8 |
| Parameter Accordion | ✅ #1,#6 | ✅ Suite 5,7 | ✅ Sec 2,9 | - |
| Direct Param Reads | ✅ #2,#3 | ✅ Suite 6 | ✅ Sec 3 | - |
| Volume Control | ✅ #11 | - | - | ✅ Test 1 |
| Mute/Solo | ✅ #12 | - | - | ✅ Test 3 |
| Send Control | ✅ #13 | - | - | ✅ Test 4 |
| Error Handling | ✅ #10 | ✅ Suite 8 | ✅ Sec 6 | ✅ Test 7 |

---

## 🎓 For New Testers

**If you're new to testing this project, follow this order:**

1. **Read:** [FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md) (10 min)
   - Understand what features exist

2. **Setup:** Prerequisites section from [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md) (5 min)
   - Get environment running

3. **Run:** [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md) - Tests #1-5 (5 min)
   - Get hands-on experience

4. **Reference:** [VISUAL_TESTING_GUIDE.md](./VISUAL_TESTING_GUIDE.md) (15 min)
   - Learn what UI should look like

5. **Deep Dive:** [WEB_UI_FEATURE_TEST_PLAN.md](./WEB_UI_FEATURE_TEST_PLAN.md) (45 min)
   - Comprehensive testing

**Total onboarding time:** ~90 minutes

---

## 🔄 Continuous Integration

### Recommended CI Pipeline

1. **PR Checks:**
   - Run: [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md) - Tests #1-5
   - Time: 5 minutes
   - Block merge if fail

2. **Nightly Tests:**
   - Run: [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md) - Full checklist
   - Time: 10 minutes
   - Alert on fail

3. **Weekly Regression:**
   - Run: [INTENTS_CHAT_INTEGRATION_TEST.md](./INTENTS_CHAT_INTEGRATION_TEST.md)
   - Time: 20 minutes
   - Report trends

4. **Pre-Release:**
   - Run: All test documents
   - Time: 90 minutes
   - Must pass 100%

---

## 📞 Support

**Questions about testing?**
- Check [FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md) for feature details
- Check [VISUAL_TESTING_GUIDE.md](./VISUAL_TESTING_GUIDE.md) for UI expectations
- Check test document debugging sections

**Found a bug?**
- Use bug reporting template above
- Reference the test document that revealed it
- Include repro steps from test

**Test failing unexpectedly?**
- Check known issues in [FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md)
- Verify prerequisites (Live running, server running, etc.)
- Check server logs for errors

---

## 📝 Maintaining Test Docs

**When adding new features:**
1. Update [FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md) with feature description
2. Add tests to [WEB_UI_FEATURE_TEST_PLAN.md](./WEB_UI_FEATURE_TEST_PLAN.md)
3. Add critical path tests to [QUICK_TEST_CHECKLIST.md](./QUICK_TEST_CHECKLIST.md)
4. Add visual expectations to [VISUAL_TESTING_GUIDE.md](./VISUAL_TESTING_GUIDE.md)
5. Update this README with new test coverage

**When fixing bugs:**
1. Add regression test to appropriate doc
2. Update known issues if applicable
3. Update visual guide if UI changed

---

**Last Updated:** 2025-10-17
**Document Version:** 1.0
**Maintainer:** _______________
