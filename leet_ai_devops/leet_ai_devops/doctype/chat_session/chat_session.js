frappe.ui.form.on('Chat Session', {
  refresh(frm) {
    frm.add_custom_button(__('Generate Proposed Changes'), async () => {
      if (!frm.doc.latest_prompt) {
        frappe.msgprint('Please add a prompt first.');
        return;
      }
      await frappe.call({
        method: 'leet_ai_devops.api.devops.generate_proposed_changes',
        args: { chat_session: frm.doc.name }
      });
      await frm.reload_doc();
      frappe.show_alert({message: 'Proposed changes updated.', indicator: 'green'});
    }).addClass('btn-primary');

    frm.add_custom_button(__('Apply All'), async () => {
      await frappe.call({
        method: 'leet_ai_devops.api.devops.apply_all',
        args: { chat_session: frm.doc.name }
      });
      await frm.reload_doc();
      frappe.show_alert({message: 'Applied all unapplied changes.', indicator: 'green'});
    });

    // Render diff blocks nicely
    if (frm.fields_dict.proposed_changes && frm.doc.proposed_changes) {
      setTimeout(() => {
        (frm.doc.proposed_changes || []).forEach((row, idx) => {
          const grid_row = frm.fields_dict.proposed_changes.grid.get_row(idx);
          if (!grid_row) return;
          const $diff = $(grid_row.grid_form.fields_dict.diff.$wrapper).find('textarea');
          if ($diff.length) $diff.addClass('leet-diff');
        });
      }, 300);
    }
  }
});

// Add Apply button on each child row form
frappe.ui.form.on('Proposed Change', {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button(__('Apply This Change'), async () => {
      await frappe.call({
        method: 'leet_ai_devops.api.devops.apply_change_row',
        args: { rowname: frm.doc.name }
      });
      await frm.reload_doc();
      frappe.show_alert({message: 'Change applied.', indicator: 'green'});
    }).addClass('btn-success');
  }
});