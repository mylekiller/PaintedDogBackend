'use strict';

var AWS = require('aws-sdk');
var dynamo = new AWS.DynamoDB.DocumentClient({region: 'us-east-2'});

exports.hello = function(event, context) {
    var file_path = decodeURIComponent(event.Records[0].s3.object.key.replace(/\+/g, ' '));
    var gallery = file_path.split("/")[0];
    var dogname = file_path.split("/")[1];
    var test = {
        TableName: 'dogs',
        Key: {
            "packName": gallery,
            "dogName": dogname,
        }
    };

    var add = true;
    dynamo.get(test, function(err, data) {
        if (err) {
            console.log(err);
        }
        else {
            if (data.Item == null) {
                if (gallery != "processed") {
                    var params = {
                        TableName: 'dogs',
                        Key: {
                            "packName": gallery,
                            "dogName": dogname,
                        },
                        UpdateExpression: "SET picture = list_append(if_not_exists(picture, :empty_list), :my_value), coords = list_append(if_not_exists(coords, :empty_list), :coord_value)",
                        ExpressionAttributeValues: {
                            ":my_value":[file_path.split("/")[2]],
                            ":empty_list":[],
                            ":coord_value":["0,0"]
                        }
                    };
                dynamo.update(params, context.done);
                }
            }
            else {
                var list = data.Item.picture
                for (var i = 0; i < list.length; i++) {
                    if (list[i] == file_path.split("/")[2]) {
                        add = false;
                        console.log("skipping adding of picture to db");
                    }
                }
                if (add) {
                    if (gallery != "processed") {
                        var params = {
                            TableName: 'dogs',
                            Key: {
                                "packName": gallery,
                                "dogName": dogname,
                            },
                            UpdateExpression: "SET picture = list_append(if_not_exists(picture, :empty_list), :my_value), coords = list_append(if_not_exists(coords, :empty_list), :coord_value)",
                            ExpressionAttributeValues: {
                                ":my_value":[file_path.split("/")[2]],
                                ":empty_list":[],
                                ":coord_value":["0,0"]
                            }
                        };
                        dynamo.update(params, context.done);
                    }
                }
            }
        }
    });
};