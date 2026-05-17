/**
 * PA1417 – Assignment 4: GUI Testing
 * Requirement 8: To-do item management — create (R8UC1), toggle (R8UC2), delete (R8UC3)
 *
 * Prerequisites before running:
 *   1. Start backend:  cd backend && python main.py
 *   2. Start frontend: cd frontend && npm start
 *   Then open Cypress: cd frontend && npx cypress open
 */

describe('R8 – To-do item management', () => {

  let uid    // user _id.$oid
  let email  // user email

  // ── helpers ──────────────────────────────────────────────────────────────────

  const loginAndOpenTask = () => {
    cy.visit('http://localhost:3000')
    cy.get('input#email').type(email)
    cy.get('form').submit()

    cy.contains('.title-overlay', 'Cypress E2E Task')
      .closest('.container-element')
      .find('a')
      .click()

    cy.get('.popup').should('be.visible')
    cy.get('.todo-list').should('exist')
  }

  const addTodo = (text) => {
    cy.get('input[placeholder="Add a new todo item"]').clear().type(text)
    cy.contains('input[type=submit]', 'Add').click()
    cy.contains('.todo-item', text).should('exist')
  }

  // ── lifecycle ─────────────────────────────────────────────────────────────────

  before(function () {
    cy.fixture('user.json').then((user) => {
      email = user.email

      cy.request({
        method: 'POST',
        url: 'http://localhost:5000/users/create',
        form: true,
        body: user,
      }).then((userResp) => {
        uid = userResp.body._id.$oid

        cy.fixture('task.json').then((task) => {
          // Build raw URL-encoded body so todos array is sent correctly
          const body =
            `title=${encodeURIComponent(task.title)}` +
            `&description=${encodeURIComponent(task.description)}` +
            `&url=${encodeURIComponent(task.url)}` +
            `&userid=${encodeURIComponent(uid)}` +
            task.todos.map(t => `&todos=${encodeURIComponent(t)}`).join('')

          cy.request({
            method: 'POST',
            url: 'http://localhost:5000/tasks/create',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: body,
          })
        })
      })
    })
  })

  after(function () {
    cy.request({
      method: 'DELETE',
      url: `http://localhost:5000/users/${uid}`,
    })
  })

  // Clean up todos between tests to ensure test isolation
  afterEach(function () {
    if (!uid) return
    cy.request({
      method: 'GET',
      url: `http://localhost:5000/tasks/ofuser/${uid}`,
      failOnStatusCode: false,
    }).then((resp) => {
      if (resp.status === 200 && Array.isArray(resp.body)) {
        resp.body.forEach((task) => {
          if (task.todos && Array.isArray(task.todos)) {
            task.todos.forEach((todo) => {
              const todoId = todo._id?.$oid ?? todo._id
              cy.request({
                method: 'DELETE',
                url: `http://localhost:5000/todos/byid/${todoId}`,
                failOnStatusCode: false,
              })
            })
          }
        })
      }
    })
  })

  // ════════════════════════════════════════════════════════════════════════════
  // R8UC1 – Create a to-do item
  // ════════════════════════════════════════════════════════════════════════════

  describe('R8UC1 – Create a to-do item', () => {

    it('TC-R8UC1-01: adds a new todo item with a valid description', () => {
      loginAndOpenTask()
      addTodo('My first todo item')
      cy.get('.todo-list').should('contain.text', 'My first todo item')
    })

    it('TC-R8UC1-02: can add multiple independent todo items', () => {
      loginAndOpenTask()
      addTodo('Todo alpha')
      addTodo('Todo beta')
      cy.get('.todo-list').should('contain.text', 'Todo alpha')
      cy.get('.todo-list').should('contain.text', 'Todo beta')
    })

    it('TC-R8UC1-03: clears the input field after adding a todo', () => {
      loginAndOpenTask()
      cy.get('input[placeholder="Add a new todo item"]').type('Temp item')
      cy.contains('input[type=submit]', 'Add').click()
      cy.contains('.todo-item', 'Temp item').should('exist')
      cy.get('input[placeholder="Add a new todo item"]').should('have.value', '')
    })

  })

  // ════════════════════════════════════════════════════════════════════════════
  // R8UC2 – Toggle the done-status of a to-do item
  // ════════════════════════════════════════════════════════════════════════════

  describe('R8UC2 – Toggle the done-status of a to-do item', () => {

    it('TC-R8UC2-01: marks a todo as done when the checker is clicked', () => {
      loginAndOpenTask()
      addTodo('Toggle to done')
      cy.contains('.todo-item', 'Toggle to done')
        .find('.checker')
        .should('have.class', 'unchecked')
        .click()
      cy.contains('.todo-item', 'Toggle to done')
        .find('.checker')
        .should('have.class', 'checked')
    })

    it('TC-R8UC2-02: unmarks a done todo when the checker is clicked again', () => {
      loginAndOpenTask()
      addTodo('Toggle back')
      cy.contains('.todo-item', 'Toggle back').find('.checker').click()
      cy.contains('.todo-item', 'Toggle back')
        .find('.checker').should('have.class', 'checked')
      cy.contains('.todo-item', 'Toggle back').find('.checker').click()
      cy.contains('.todo-item', 'Toggle back')
        .find('.checker').should('have.class', 'unchecked')
    })

    it('TC-R8UC2-03: does not change the state of other todo items', () => {
      loginAndOpenTask()
      addTodo('Item stays unchecked')
      addTodo('Item gets checked')
      cy.contains('.todo-item', 'Item gets checked').find('.checker').click()
      cy.contains('.todo-item', 'Item stays unchecked')
        .find('.checker')
        .should('have.class', 'unchecked')
    })

  })

  // ════════════════════════════════════════════════════════════════════════════
  // R8UC3 – Delete a to-do item
  // Note: TC-R8UC3-01, 02, 03 reveal a real defect — the DELETE request
  // succeeds (HTTP 200) but the UI does not re-render because deleteTodo()
  // in TaskDetail.js calls updateTask() as a value rather than a callback.
  // ════════════════════════════════════════════════════════════════════════════

  describe('R8UC3 – Delete a to-do item', () => {

    it('TC-R8UC3-01: removes a todo from the list when the remover is clicked', () => {
      loginAndOpenTask()
      addTodo('Delete me')
      cy.contains('.todo-item', 'Delete me').find('.remover').click()
      cy.get('.todo-list', { timeout: 6000 })
        .should('not.contain.text', 'Delete me')
    })

    it('TC-R8UC3-02: only removes the targeted todo and leaves others intact', () => {
      loginAndOpenTask()
      addTodo('Keep me')
      addTodo('Remove me')
      cy.contains('.todo-item', 'Remove me').find('.remover').click()
      cy.get('.todo-list', { timeout: 6000 })
        .should('not.contain.text', 'Remove me')
      cy.get('.todo-list').should('contain.text', 'Keep me')
    })

    it('TC-R8UC3-03: can delete a todo that has been marked as done', () => {
      loginAndOpenTask()
      addTodo('Done then deleted')
      cy.contains('.todo-item', 'Done then deleted').find('.checker').click()
      cy.contains('.todo-item', 'Done then deleted')
        .find('.checker').should('have.class', 'checked')
      cy.contains('.todo-item', 'Done then deleted').find('.remover').click()
      cy.get('.todo-list', { timeout: 6000 })
        .should('not.contain.text', 'Done then deleted')
    })

  })

})
