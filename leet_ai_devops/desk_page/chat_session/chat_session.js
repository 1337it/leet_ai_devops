frappe.pages['chat-session'].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: 'Chat Session',
    single_column: true
  });

  // Simple redirect to the Chat Session list so the route works:
  frappe.set_route('List', 'Chat Session');
};