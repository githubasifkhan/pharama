

from odoo.exceptions import Warning
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    review_by_id = fields.Many2one('res.users', string='Reviewed By')
    approve_by_id = fields.Many2one('res.users', string='Approved By')

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to_review', 'Waiting For Review'),
        ('approve', 'Waiting For Approval'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    def button_confirm(self):
        self.write({
            'state': 'to_review'
        })

    def button_review(self):
        if self.env.user.has_group('manager_all_approvals.group_review_purchase_order'):
            self.review_by_id = self.env.user.id
        self.write({
            'state': 'approve'
        })

    def action_reject(self):
        self.write({
            'state': 'rejected'
        })

    def button_approved(self):
        if self.env.user.has_group('manager_all_approvals.group_approve_purchase_order'):
            self.approve_by_id = self.env.user.id
        for order in self:
            if order.state not in ['draft', 'sent', 'approve']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.company.currency_id._convert(
                        order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                        order.date_order or fields.Date.today())) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def button_reject(self):
        self.write({
            'state': 'rejected'
        })


class SaleOrderInh(models.Model):
    _inherit = 'sale.order'

    review_by_id = fields.Many2one('res.users', string='Reviewed By')
    approve_by_id = fields.Many2one('res.users', string='Approved By')

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('to_review', 'Waiting For Review'),
        ('approve', 'Waiting For Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    def action_confirm(self):
        self.write({
            'state': 'to_review'
        })

    def button_review(self):
        if self.env.user.has_group('manager_all_approvals.group_review_sale_order'):
            self.review_by_id = self.env.user.id
        self.write({
            'state': 'approve'
        })

    def action_reject(self):
        self.write({
            'state': 'rejected'
        })

    def button_approved(self):
        if self.env.user.has_group('manager_all_approvals.group_approve_sale_order'):
            self.approve_by_id = self.env.user.id
        rec = super(SaleOrderInh, self).action_confirm()
        return rec

    def button_reject(self):
        self.write({
            'state': 'rejected'
        })


# class MRPProductionInh(models.Model):
#     _inherit = 'mrp.production'
#
#     review_by_id = fields.Many2one('res.users', string='Reviewed By')
#     approve_by_id = fields.Many2one('res.users', string='Approved By')
#
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('confirmed', 'Confirmed'),
#         ('progress', 'In Progress'),
#         ('to_close', 'To Close'),
#         ('to_review', 'Waiting For Review'),
#         ('approve', 'Waiting For Approval'),
#         ('done', 'Done'),
#         ('cancel', 'Cancelled'),
#         ('rejected', 'Rejected'),], string='State',
#         compute='_compute_state', copy=False, index=True, readonly=True,
#         store=True, tracking=True,
#         help=" * Draft: The MO is not confirmed yet.\n"
#              " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
#              " * In Progress: The production has started (on the MO or on the WO).\n"
#              " * To Close: The production is done, the MO has to be closed.\n"
#              " * Done: The MO is closed, the stock moves are posted. \n"
#              " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")
#
#     def button_mark_done(self):
#         self.write({
#             'state': 'to_review'
#         })
#
#     def button_review(self):
#         if self.env.user.has_group('manager_all_approvals.group_review_mrp'):
#             self.review_by_id = self.env.user.id
#         self.write({
#             'state': 'approve'
#         })
#
#     def action_reject(self):
#         self.write({
#             'state': 'rejected'
#         })
#
#     # def button_approved(self):
#     #     if self.env.user.has_group('manager_all_approvals.group_approve_mrp'):
#     #         self.approve_by_id = self.env.user.id
#     #     rec = super(MRPProductionInh, self).button_mark_done()
#     #     return rec
#
#     def button_reject(self):
#         self.write({
#             'state': 'rejected'
#         })
#
#     def button_approved(self):
#         orders_to_plan = self.filtered(lambda order: order.routing_id and order.state == 'approve')
#         for order in orders_to_plan:
#             order.move_raw_ids.filtered(lambda m: m.state == 'draft')._action_confirm()
#             quantity = order.product_uom_id._compute_quantity(order.product_qty,
#                                                               order.bom_id.product_uom_id) / order.bom_id.product_qty
#             boms, lines = order.bom_id.explode(order.product_id, quantity, picking_type=order.bom_id.picking_type_id)
#             order._generate_workorders(boms)
#             order._plan_workorders()
#         return True


class AccountMoveInh(models.Model):
    _inherit = 'account.move'

    review_by_id = fields.Many2one('res.users', string='Reviewed By')
    approve_by_id = fields.Many2one('res.users', string='Approved By')

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('to_review', 'Waiting For Review'),
        ('approve', 'Waiting For Approval'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True, default='draft')

    def action_post(self):
        self.write({
            'state': 'to_review'
        })

    def button_review(self):
        if self.env.user.has_group('manager_all_approvals.group_review_invoice_bill'):
            self.review_by_id = self.env.user.id
        self.write({
            'state': 'approve'
        })

    def action_reject(self):
        self.write({
            'state': 'rejected'
        })

    def button_approved(self):
        if self.env.user.has_group('manager_all_approvals.group_approve_invoice_bill'):
            self.approve_by_id = self.env.user.id
        rec = super(AccountMoveInh, self).action_post()
        return rec

    def button_reject(self):
        self.write({
            'state': 'rejected'
        })


class AccountPaymentInh(models.Model):
    _inherit = 'account.payment'

    review_by_id = fields.Many2one('res.users', string='Reviewed By')
    approve_by_id = fields.Many2one('res.users', string='Approved By')

    # state = fields.Selection([('draft', 'Draft'),
    #                           ('approve', 'Waiting For Approval'),
    #                           ('posted', 'Validated'),
    #                           ('sent', 'Sent'),
    #                           ('reconciled', 'Reconciled'),
    #                           ('cancelled', 'Cancelled'),
    #                           ('reject', 'Reject')
    #                           ], readonly=True, default='draft', copy=False, string="Status")

    def action_post(self):
        self.write({
            'state': 'to_review'
        })

    def button_review(self):
        if self.env.user.has_group('manager_all_approvals.group_review_payment'):
            self.review_by_id = self.env.user.id
        self.write({
            'state': 'approve'
        })

    def action_reject(self):
        self.write({
            'state': 'rejected'
        })

    def button_approved(self):
        if self.env.user.has_group('manager_all_approvals.group_approve_payment'):
            self.approve_by_id = self.env.user.id
        rec = super(AccountPaymentInh, self).action_post()
        return rec

    def button_reject(self):
        self.write({
            'state': 'rejected'
        })


    # def button_approve(self):
        # AccountMove = self.env['account.move'].with_context(default_type='entry')
        # for rec in self:
        #
        #     if rec.state != 'approve':
        #         raise UserError(_("Only a draft payment can be posted."))
        #
        #     if any(inv.state != 'posted' for inv in rec.invoice_ids):
        #         raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
        #
        #     # keep the name in case of a payment reset to draft
        #     if not rec.name:
        #         # Use the right sequence to set the name
        #         if rec.payment_type == 'transfer':
        #             sequence_code = 'account.payment.transfer'
        #         else:
        #             if rec.partner_type == 'customer':
        #                 if rec.payment_type == 'inbound':
        #                     sequence_code = 'account.payment.customer.invoice'
        #                 if rec.payment_type == 'outbound':
        #                     sequence_code = 'account.payment.customer.refund'
        #             if rec.partner_type == 'supplier':
        #                 if rec.payment_type == 'inbound':
        #                     sequence_code = 'account.payment.supplier.refund'
        #                 if rec.payment_type == 'outbound':
        #                     sequence_code = 'account.payment.supplier.invoice'
        #         rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
        #         if not rec.name and rec.payment_type != 'transfer':
        #             raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
        #
        #     moves = AccountMove.create(rec._prepare_payment_moves())
        #     moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
        #
        #     # Update the state / move before performing any reconciliation.
        #     move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
        #     rec.write({'state': 'posted', 'move_name': move_name})
        #
        #     if rec.payment_type in ('inbound', 'outbound'):
        #         # ==== 'inbound' / 'outbound' ====
        #         if rec.invoice_ids:
        #             (moves[0] + rec.invoice_ids).line_ids \
        #                 .filtered(
        #                 lambda line: not line.reconciled and line.account_id == rec.destination_account_id and not (
        #                             line.account_id == line.payment_id.writeoff_account_id and line.name == line.payment_id.writeoff_label)) \
        #                 .reconcile()
        #     elif rec.payment_type == 'transfer':
        #         # ==== 'transfer' ====
        #         moves.mapped('line_ids') \
        #             .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
        #             .reconcile()
        #
        # return True


# class StockPickingInh(models.Model):
#     _inherit = 'stock.picking'
#
#     review_by_id = fields.Many2one('res.users', string='Reviewed By')
#     approve_by_id = fields.Many2one('res.users', string='Approved By')
#
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('waiting', 'Waiting Another Operation'),
#         ('confirmed', 'Waiting'),
#         ('assigned', 'Ready'),
#         ('to_review', 'Waiting For Review'),
#         ('approve', 'Waiting For Approval'),
#         ('done', 'Done'),
#         ('cancel', 'Cancelled'),
#         ('rejected', 'Rejected'),
#     ], string='Status', compute='_compute_state',
#         copy=False, index=True, readonly=True, store=True, tracking=True,
#         help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
#              " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
#              " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
#              " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
#              " * Done: The transfer has been processed.\n"
#              " * Cancelled: The transfer has been cancelled.")
#
#     def button_validate(self):
#         self.write({
#             'state': 'to_review'
#         })
#
#     def button_review(self):
#         if self.env.user.has_group('manager_all_approvals.group_review_transfer'):
#             self.review_by_id = self.env.user.id
#         self.write({
#             'state': 'approve'
#         })
#
#     def action_reject(self):
#         self.write({
#             'state': 'rejected'
#         })
#
#     def button_approved(self):
#         if self.env.user.has_group('manager_all_approvals.group_approve_transfer'):
#             self.approve_by_id = self.env.user.id
#         # rec = super(StockPickingInh, self).button_validate()
#         # return rec
#         # Clean-up the context key at validation to avoid forcing the creation of immediate
#         # transfers.
#         ctx = dict(self.env.context)
#         ctx.pop('default_immediate_transfer', None)
#         self = self.with_context(ctx)
#         # Sanity checks.
#         pickings_without_moves = self.browse()
#         pickings_without_quantities = self.browse()
#         pickings_without_lots = self.browse()
#         products_without_lots = self.env['product.product']
#         for picking in self:
#             if not picking.move_lines and not picking.move_line_ids:
#                 pickings_without_moves |= picking
#
#             picking.message_subscribe([self.env.user.partner_id.id])
#             picking_type = picking.picking_type_id
#             precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
#             no_quantities_done = all(
#                 float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in
#                 picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
#             no_reserved_quantities = all(
#                 float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for
#                 move_line in picking.move_line_ids)
#             if no_reserved_quantities and no_quantities_done:
#                 pickings_without_quantities |= picking
#
#             if picking_type.use_create_lots or picking_type.use_existing_lots:
#                 lines_to_check = picking.move_line_ids
#                 if not no_quantities_done:
#                     lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0,
#                                                                                         precision_rounding=line.product_uom_id.rounding))
#                 for line in lines_to_check:
#                     product = line.product_id
#                     if product and product.tracking != 'none':
#                         if not line.lot_name and not line.lot_id:
#                             pickings_without_lots |= picking
#                             products_without_lots |= product
#
#         if not self._should_show_transfers():
#             if pickings_without_moves:
#                 raise UserError(_('Please add some items to move.'))
#             if pickings_without_quantities:
#                 raise UserError(self._get_without_quantities_error_message())
#             if pickings_without_lots:
#                 raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(
#                     products_without_lots.mapped('display_name')))
#         else:
#             message = ""
#             if pickings_without_moves:
#                 message += _('Transfers %s: Please add some items to move.') % ', '.join(
#                     pickings_without_moves.mapped('name'))
#             if pickings_without_quantities:
#                 message += _(
#                     '\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(
#                     pickings_without_quantities.mapped('name'))
#             if pickings_without_lots:
#                 message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (
#                 ', '.join(pickings_without_lots.mapped('name')),
#                 ', '.join(products_without_lots.mapped('display_name')))
#             if message:
#                 raise UserError(message.lstrip())
#
#         # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
#         # moves and/or the context and never call `_action_done`.
#         if not self.env.context.get('button_validate_picking_ids'):
#             self = self.with_context(button_validate_picking_ids=self.ids)
#         res = self._pre_action_done_hook()
#         if res is not True:
#             return res
#
#         # Call `_action_done`.
#         if self.env.context.get('picking_ids_not_to_backorder'):
#             pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
#             pickings_to_backorder = self - pickings_not_to_backorder
#         else:
#             pickings_not_to_backorder = self.env['stock.picking']
#             pickings_to_backorder = self
#         pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
#         pickings_to_backorder.with_context(cancel_backorder=False)._action_done()
#         return True
#
#     def button_reject(self):
#         self.write({
#             'state': 'rejected'
#         })




