from marshmallow import Schema, fields, validate

class BanUserSchema(Schema):
    admin_id = fields.Integer(required=True)
    reason = fields.String(required=True, validate=validate.Length(min=5, max=200))

class CreateModeratorSchema(Schema):
    admin_id = fields.Integer(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))
    full_name = fields.String(required=True, validate=validate.Length(min=2))

class CreateAdminSchema(Schema):
    admin_id = fields.Integer(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))
    full_name = fields.String(required=True, validate=validate.Length(min=2))

class ResolveReportSchema(Schema):
    admin_id = fields.Integer(required=True)
    status = fields.String(required=False, validate=validate.OneOf(["resolved", "dismissed"]))
    resolution_notes = fields.String(required=False, validate=validate.Length(max=500))
