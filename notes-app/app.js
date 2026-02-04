/**
 * Notely - Modern Notes App
 * JavaScript Application Logic
 */

// ============================================
// STATE MANAGEMENT
// ============================================
class NotesApp {
    constructor() {
        this.notes = [];
        this.activeNoteId = null;
        this.autoSaveTimeout = null;
        
        // DOM Elements
        this.elements = {
            notesList: document.getElementById('notesList'),
            notesCount: document.getElementById('notesCount'),
            searchInput: document.getElementById('searchInput'),
            newNoteBtn: document.getElementById('newNoteBtn'),
            createFirstBtn: document.getElementById('createFirstBtn'),
            emptyState: document.getElementById('emptyState'),
            noteEditor: document.getElementById('noteEditor'),
            noteTitleInput: document.getElementById('noteTitleInput'),
            editorContent: document.getElementById('editorContent'),
            lastEdited: document.getElementById('lastEdited'),
            deleteNoteBtn: document.getElementById('deleteNoteBtn'),
            deleteModal: document.getElementById('deleteModal'),
            cancelDelete: document.getElementById('cancelDelete'),
            confirmDelete: document.getElementById('confirmDelete'),
            formatBtns: document.querySelectorAll('.format-btn')
        };
        
        this.init();
    }
    
    // ============================================
    // INITIALIZATION
    // ============================================
    init() {
        this.loadNotes();
        this.bindEvents();
        this.render();
    }
    
    bindEvents() {
        // New note buttons
        this.elements.newNoteBtn.addEventListener('click', () => this.createNote());
        this.elements.createFirstBtn.addEventListener('click', () => this.createNote());
        
        // Search
        this.elements.searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        
        // Editor events
        this.elements.noteTitleInput.addEventListener('input', () => this.handleTitleChange());
        this.elements.editorContent.addEventListener('input', () => this.handleContentChange());
        
        // Delete note
        this.elements.deleteNoteBtn.addEventListener('click', () => this.showDeleteModal());
        this.elements.cancelDelete.addEventListener('click', () => this.hideDeleteModal());
        this.elements.confirmDelete.addEventListener('click', () => this.deleteNote());
        
        // Close modal on outside click
        this.elements.deleteModal.addEventListener('click', (e) => {
            if (e.target === this.elements.deleteModal) {
                this.hideDeleteModal();
            }
        });
        
        // Formatting toolbar
        this.elements.formatBtns.forEach(btn => {
            btn.addEventListener('click', () => this.handleFormat(btn.dataset.command));
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    // ============================================
    // DATA PERSISTENCE
    // ============================================
    loadNotes() {
        try {
            const saved = localStorage.getItem('notely-notes');
            this.notes = saved ? JSON.parse(saved) : [];
        } catch (error) {
            console.error('Error loading notes:', error);
            this.notes = [];
        }
    }
    
    saveNotes() {
        try {
            localStorage.setItem('notely-notes', JSON.stringify(this.notes));
        } catch (error) {
            console.error('Error saving notes:', error);
        }
    }
    
    // ============================================
    // NOTE OPERATIONS
    // ============================================
    createNote() {
        const note = {
            id: this.generateId(),
            title: '',
            content: '',
            createdAt: Date.now(),
            updatedAt: Date.now()
        };
        
        this.notes.unshift(note);
        this.saveNotes();
        this.selectNote(note.id);
        this.render();
        
        // Focus on title input
        setTimeout(() => {
            this.elements.noteTitleInput.focus();
        }, 100);
    }
    
    selectNote(id) {
        this.activeNoteId = id;
        const note = this.getActiveNote();
        
        if (note) {
            this.elements.emptyState.style.display = 'none';
            this.elements.noteEditor.style.display = 'flex';
            this.elements.noteTitleInput.value = note.title;
            this.elements.editorContent.innerHTML = note.content;
            this.updateLastEdited(note.updatedAt);
        }
        
        this.updateNotesList();
    }
    
    deleteNote() {
        if (!this.activeNoteId) return;
        
        this.notes = this.notes.filter(note => note.id !== this.activeNoteId);
        this.saveNotes();
        this.hideDeleteModal();
        
        // Select next note or show empty state
        if (this.notes.length > 0) {
            this.selectNote(this.notes[0].id);
        } else {
            this.activeNoteId = null;
            this.showEmptyState();
        }
        
        this.render();
    }
    
    getActiveNote() {
        return this.notes.find(note => note.id === this.activeNoteId);
    }
    
    // ============================================
    // EVENT HANDLERS
    // ============================================
    handleTitleChange() {
        const note = this.getActiveNote();
        if (!note) return;
        
        note.title = this.elements.noteTitleInput.value;
        note.updatedAt = Date.now();
        
        this.autoSave();
        this.updateNotesList();
    }
    
    handleContentChange() {
        const note = this.getActiveNote();
        if (!note) return;
        
        note.content = this.elements.editorContent.innerHTML;
        note.updatedAt = Date.now();
        
        this.autoSave();
        this.updateNotesList();
        this.updateLastEdited(note.updatedAt);
    }
    
    handleSearch(query) {
        const normalizedQuery = query.toLowerCase().trim();
        
        if (!normalizedQuery) {
            this.render();
            return;
        }
        
        const filtered = this.notes.filter(note => 
            note.title.toLowerCase().includes(normalizedQuery) ||
            this.stripHtml(note.content).toLowerCase().includes(normalizedQuery)
        );
        
        this.renderNotesList(filtered);
    }
    
    handleFormat(command) {
        if (command === 'heading') {
            document.execCommand('formatBlock', false, 'h2');
        } else {
            document.execCommand(command, false, null);
        }
        
        this.elements.editorContent.focus();
        this.handleContentChange();
    }
    
    handleKeyboard(e) {
        // Ctrl/Cmd + N: New note
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            this.createNote();
        }
        
        // Escape: Close modal
        if (e.key === 'Escape') {
            this.hideDeleteModal();
        }
    }
    
    // ============================================
    // AUTO-SAVE
    // ============================================
    autoSave() {
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            this.saveNotes();
        }, 300);
    }
    
    // ============================================
    // RENDERING
    // ============================================
    render() {
        this.updateNotesCount();
        this.renderNotesList(this.notes);
        
        if (this.notes.length === 0) {
            this.showEmptyState();
        } else if (!this.activeNoteId) {
            this.showEmptyState();
        }
    }
    
    renderNotesList(notes) {
        this.elements.notesList.innerHTML = notes.map(note => `
            <li class="note-item ${note.id === this.activeNoteId ? 'active' : ''}" 
                data-id="${note.id}"
                onclick="app.selectNote('${note.id}')">
                <div class="note-item-title">${this.escapeHtml(note.title) || 'Untitled Note'}</div>
                <div class="note-item-preview">${this.getPreview(note.content)}</div>
                <div class="note-item-date">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    ${this.formatDate(note.updatedAt)}
                </div>
            </li>
        `).join('');
    }
    
    updateNotesList() {
        const items = this.elements.notesList.querySelectorAll('.note-item');
        items.forEach(item => {
            const id = item.dataset.id;
            const note = this.notes.find(n => n.id === id);
            
            if (note) {
                item.classList.toggle('active', id === this.activeNoteId);
                item.querySelector('.note-item-title').textContent = note.title || 'Untitled Note';
                item.querySelector('.note-item-preview').textContent = this.getPreview(note.content);
            }
        });
    }
    
    updateNotesCount() {
        this.elements.notesCount.textContent = this.notes.length;
    }
    
    updateLastEdited(timestamp) {
        this.elements.lastEdited.textContent = this.formatDate(timestamp);
    }
    
    showEmptyState() {
        this.elements.emptyState.style.display = 'flex';
        this.elements.noteEditor.style.display = 'none';
    }
    
    showDeleteModal() {
        this.elements.deleteModal.classList.add('active');
    }
    
    hideDeleteModal() {
        this.elements.deleteModal.classList.remove('active');
    }
    
    // ============================================
    // UTILITIES
    // ============================================
    generateId() {
        return 'note-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    stripHtml(html) {
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
    }
    
    getPreview(content) {
        const text = this.stripHtml(content);
        return text.length > 60 ? text.substring(0, 60) + '...' : text || 'No content';
    }
    
    formatDate(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        // Less than 1 minute
        if (diff < 60000) {
            return 'Just now';
        }
        
        // Less than 1 hour
        if (diff < 3600000) {
            const mins = Math.floor(diff / 60000);
            return `${mins} min${mins > 1 ? 's' : ''} ago`;
        }
        
        // Less than 24 hours
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        }
        
        // Less than 7 days
        if (diff < 604800000) {
            const days = Math.floor(diff / 86400000);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        }
        
        // Fallback to date
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        });
    }
}

// Initialize the app
const app = new NotesApp();
