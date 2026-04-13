// Sliples UI Recorder v1.0
// Usage: Include this script, then call:
//   SliplesRecorder.configure({ apiKey: 'your-key', endpoint: 'https://your-sliples-server/api/v1' });
//   SliplesRecorder.start('My Test Recording');
//   // ... interact with the page ...
//   SliplesRecorder.stop();

(function() {
  'use strict';

  const SliplesRecorder = {
    config: {
      apiKey: null,
      endpoint: '/api/v1',
      projectId: null,
    },
    sessionId: null,
    events: [],
    sequence: 0,
    isRecording: false,
    flushInterval: null,

    configure: function(options) {
      Object.assign(this.config, options);
      console.log('[Sliples] Configured with endpoint:', this.config.endpoint);
      return this;
    },

    // Generate CSS selector for an element
    getCssSelector: function(el) {
      if (!el || el === document.body) return 'body';
      if (el.id) return '#' + CSS.escape(el.id);

      const path = [];
      while (el && el !== document.body) {
        let selector = el.tagName.toLowerCase();
        if (el.id) {
          selector = '#' + CSS.escape(el.id);
          path.unshift(selector);
          break;
        }
        if (el.className && typeof el.className === 'string') {
          const classes = el.className.trim().split(/\s+/).filter(c => c && !c.match(/^(hover|active|focus|ng-|\d)/));
          if (classes.length) selector += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
        }
        const parent = el.parentElement;
        if (parent) {
          const siblings = Array.from(parent.children).filter(c => c.tagName === el.tagName);
          if (siblings.length > 1) {
            const index = siblings.indexOf(el) + 1;
            selector += ':nth-of-type(' + index + ')';
          }
        }
        path.unshift(selector);
        el = parent;
      }
      return path.join(' > ');
    },

    // Generate XPath for an element
    getXPath: function(el) {
      if (!el) return '';
      if (el.id) return '//*[@id="' + el.id + '"]';

      const parts = [];
      while (el && el.nodeType === Node.ELEMENT_NODE) {
        let index = 1;
        let sibling = el.previousSibling;
        while (sibling) {
          if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === el.tagName) index++;
          sibling = sibling.previousSibling;
        }
        parts.unshift(el.tagName.toLowerCase() + '[' + index + ']');
        el = el.parentNode;
      }
      return '/' + parts.join('/');
    },

    // Get associated label text
    getLabelText: function(el) {
      if (el.labels && el.labels.length) return el.labels[0].textContent.trim();
      const ariaLabel = el.getAttribute('aria-label');
      if (ariaLabel) return ariaLabel;
      const labelledBy = el.getAttribute('aria-labelledby');
      if (labelledBy) {
        const labelEl = document.getElementById(labelledBy);
        if (labelEl) return labelEl.textContent.trim();
      }
      const parentLabel = el.closest('label');
      if (parentLabel) return parentLabel.textContent.trim();
      return null;
    },

    // Extract element metadata
    getElementData: function(el) {
      if (!el || !el.tagName) return {};
      return {
        selector_css: this.getCssSelector(el),
        selector_xpath: this.getXPath(el),
        selector_text: el.textContent ? el.textContent.trim().substring(0, 100) : null,
        selector_test_id: el.getAttribute('data-testid') || el.getAttribute('data-test-id'),
        selector_aria: el.getAttribute('aria-label'),
        tag_name: el.tagName.toLowerCase(),
        element_id: el.id || null,
        element_classes: el.className && typeof el.className === 'string' ? JSON.stringify(el.className.split(/\s+/).filter(Boolean)) : null,
        element_name: el.name || null,
        element_type: el.type || null,
        element_role: el.getAttribute('role'),
        label_text: this.getLabelText(el),
        placeholder: el.placeholder || null,
      };
    },

    // Record an event
    record: function(type, el, extra) {
      if (!this.isRecording) return;

      const event = {
        sequence: this.sequence++,
        timestamp: new Date().toISOString(),
        event_type: type,
        url: window.location.href,
        ...this.getElementData(el),
        ...extra,
      };

      this.events.push(event);
      console.log('[Sliples] Recorded:', type, event.selector_css || event.url);
    },

    // Flush events to server
    flush: async function() {
      if (!this.events.length || !this.sessionId) return;

      const batch = this.events.splice(0, this.events.length);
      try {
        const resp = await fetch(this.config.endpoint + '/recorder/sessions/' + this.sessionId + '/events', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': this.config.apiKey,
          },
          body: JSON.stringify({ events: batch }),
        });
        if (!resp.ok) console.error('[Sliples] Failed to send events:', resp.status);
      } catch (e) {
        console.error('[Sliples] Network error:', e);
        this.events.unshift(...batch);
      }
    },

    // Event handlers
    handleClick: function(e) {
      const rect = e.target.getBoundingClientRect();
      this.record('click', e.target, {
        coordinates: { x: Math.round(e.clientX - rect.left), y: Math.round(e.clientY - rect.top) },
      });
    },

    handleInput: function(e) {
      clearTimeout(e.target._sliplesTimeout);
      e.target._sliplesTimeout = setTimeout(() => {
        this.record('input', e.target, {
          value: e.target.type === 'password' ? '***' : e.target.value,
        });
      }, 500);
    },

    handleChange: function(e) {
      this.record('change', e.target, {
        value: e.target.value,
      });
    },

    handleSubmit: function(e) {
      this.record('submit', e.target);
    },

    handleKeydown: function(e) {
      if (['Enter', 'Tab', 'Escape', 'Backspace', 'Delete'].includes(e.key) || e.ctrlKey || e.metaKey) {
        this.record('keydown', e.target, {
          key_info: {
            key: e.key,
            code: e.code,
            ctrl: e.ctrlKey,
            alt: e.altKey,
            shift: e.shiftKey,
            meta: e.metaKey,
          },
        });
      }
    },

    // Start recording
    start: async function(name) {
      if (!this.config.apiKey) {
        console.error('[Sliples] API key not configured. Call SliplesRecorder.configure({ apiKey: "..." }) first.');
        return;
      }
      if (this.isRecording) {
        console.warn('[Sliples] Already recording');
        return;
      }

      const sessionName = name || 'Recording ' + new Date().toLocaleString();

      try {
        const url = this.config.endpoint + '/recorder/sessions' + (this.config.projectId ? '?project_id=' + this.config.projectId : '');
        const resp = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': this.config.apiKey,
          },
          body: JSON.stringify({
            name: sessionName,
            url: window.location.href,
            user_agent: navigator.userAgent,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight,
          }),
        });

        if (!resp.ok) throw new Error('Failed to start session: ' + resp.status);

        const data = await resp.json();
        this.sessionId = data.session_id;
        this.isRecording = true;
        this.sequence = 0;
        this.events = [];

        // Attach listeners
        document.addEventListener('click', this._handleClick, true);
        document.addEventListener('input', this._handleInput, true);
        document.addEventListener('change', this._handleChange, true);
        document.addEventListener('submit', this._handleSubmit, true);
        document.addEventListener('keydown', this._handleKeydown, true);

        // Record navigation events
        this._navObserver = new MutationObserver(() => {
          if (this._lastUrl !== window.location.href) {
            this._lastUrl = window.location.href;
            this.record('navigation', null, { url: window.location.href });
          }
        });
        this._navObserver.observe(document.body, { childList: true, subtree: true });
        this._lastUrl = window.location.href;

        // Flush periodically
        this.flushInterval = setInterval(() => this.flush(), 3000);

        console.log('[Sliples] Recording started. Session:', this.sessionId);
        console.log('[Sliples] Call SliplesRecorder.stop() to finish');

      } catch (e) {
        console.error('[Sliples] Failed to start recording:', e);
      }
    },

    // Stop recording
    stop: async function() {
      if (!this.isRecording) {
        console.warn('[Sliples] Not recording');
        return;
      }

      this.isRecording = false;

      // Remove listeners
      document.removeEventListener('click', this._handleClick, true);
      document.removeEventListener('input', this._handleInput, true);
      document.removeEventListener('change', this._handleChange, true);
      document.removeEventListener('submit', this._handleSubmit, true);
      document.removeEventListener('keydown', this._handleKeydown, true);

      if (this._navObserver) this._navObserver.disconnect();
      clearInterval(this.flushInterval);

      // Final flush
      await this.flush();

      // Stop session on server
      try {
        const resp = await fetch(this.config.endpoint + '/recorder/sessions/' + this.sessionId + '/stop', {
          method: 'POST',
          headers: { 'X-API-Key': this.config.apiKey },
        });

        if (resp.ok) {
          const data = await resp.json();
          console.log('[Sliples] Recording stopped. Events:', data.event_count);
          return data;
        }
      } catch (e) {
        console.error('[Sliples] Failed to stop recording:', e);
      }

      this.sessionId = null;
    },

    // Initialize bound handlers
    init: function() {
      this._handleClick = this.handleClick.bind(this);
      this._handleInput = this.handleInput.bind(this);
      this._handleChange = this.handleChange.bind(this);
      this._handleSubmit = this.handleSubmit.bind(this);
      this._handleKeydown = this.handleKeydown.bind(this);
      return this;
    },
  }.init();

  // Expose globally
  window.SliplesRecorder = SliplesRecorder;

  console.log('[Sliples] Recorder loaded. Call SliplesRecorder.configure({ apiKey: "..." }) then SliplesRecorder.start("Test Name")');
})();
