import { create } from 'zustand'
import * as api from '../api/client'
import type { Page, PageCreate, PageUpdate, PageOverrideCreate, PageOverride } from '../api/client'

interface PagesState {
  // State
  pages: Page[]
  selectedPage: Page | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchPages: () => Promise<void>
  fetchPage: (id: string) => Promise<void>
  createPage: (data: PageCreate) => Promise<Page>
  updatePage: (id: string, data: PageUpdate) => Promise<Page>
  deletePage: (id: string) => Promise<void>
  selectPage: (page: Page | null) => void
  addOverride: (pageId: string, data: PageOverrideCreate) => Promise<PageOverride>
  removeOverride: (pageId: string, overrideId: string) => Promise<void>
  clearError: () => void
}

export const usePagesStore = create<PagesState>((set) => ({
  // Initial state
  pages: [],
  selectedPage: null,
  isLoading: false,
  error: null,

  // Fetch all pages
  fetchPages: async () => {
    set({ isLoading: true, error: null, selectedPage: null })
    try {
      const pages = await api.listPages()
      set({ pages, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch pages:', error)
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch pages',
        isLoading: false,
      })
    }
  },

  // Fetch single page
  fetchPage: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const page = await api.getPage(id)
      set({ selectedPage: page, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch page:', error)
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch page',
        isLoading: false,
      })
    }
  },

  // Create page
  createPage: async (data: PageCreate) => {
    set({ isLoading: true, error: null })
    try {
      const page = await api.createPage(data)
      set((state) => ({
        pages: [...state.pages, page],
        isLoading: false,
      }))
      return page
    } catch (error) {
      console.error('Failed to create page:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create page'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Update page
  updatePage: async (id: string, data: PageUpdate) => {
    set({ isLoading: true, error: null })
    try {
      const page = await api.updatePage(id, data)
      set((state) => ({
        pages: state.pages.map((p) => (p.id === id ? page : p)),
        selectedPage: state.selectedPage?.id === id ? page : state.selectedPage,
        isLoading: false,
      }))
      return page
    } catch (error) {
      console.error('Failed to update page:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to update page'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Delete page
  deletePage: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.deletePage(id)
      set((state) => ({
        pages: state.pages.filter((p) => p.id !== id),
        selectedPage: state.selectedPage?.id === id ? null : state.selectedPage,
        isLoading: false,
      }))
    } catch (error) {
      console.error('Failed to delete page:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete page'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Select page
  selectPage: (page: Page | null) => {
    set({ selectedPage: page })
  },

  // Add environment override
  addOverride: async (pageId: string, data: PageOverrideCreate) => {
    set({ isLoading: true, error: null })
    try {
      const override = await api.createPageOverride(pageId, data)
      // Refresh the page to get updated overrides
      const page = await api.getPage(pageId)
      set((state) => ({
        pages: state.pages.map((p) => (p.id === pageId ? page : p)),
        selectedPage: state.selectedPage?.id === pageId ? page : state.selectedPage,
        isLoading: false,
      }))
      return override
    } catch (error) {
      console.error('Failed to add override:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to add override'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Remove environment override
  removeOverride: async (pageId: string, overrideId: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.deletePageOverride(pageId, overrideId)
      // Refresh the page to get updated overrides
      const page = await api.getPage(pageId)
      set((state) => ({
        pages: state.pages.map((p) => (p.id === pageId ? page : p)),
        selectedPage: state.selectedPage?.id === pageId ? page : state.selectedPage,
        isLoading: false,
      }))
    } catch (error) {
      console.error('Failed to remove override:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to remove override'
      set({ error: errorMessage, isLoading: false })
      throw new Error(errorMessage)
    }
  },

  // Clear error
  clearError: () => set({ error: null }),
}))
