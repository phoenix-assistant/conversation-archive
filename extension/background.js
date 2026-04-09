// Background service worker for Conversation Archive extension
// Stub — future: receive messages from content script and send to local API

chrome.action.onClicked.addListener(async (tab) => {
  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.title,
    });
    console.log("Conversation Archive: captured from", result.result);
  } catch (err) {
    console.error("Conversation Archive error:", err);
  }
});
