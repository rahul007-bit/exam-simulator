import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import App from '@/App.vue'

describe('smoke', () => {
  it('mounts the app shell', () => {
    const wrapper = mount(App, {
      global: {
        stubs: { RouterView: true },
      },
    })
    expect(wrapper.exists()).toBe(true)
  })
})
