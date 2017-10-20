const path = require('path');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const wepback = require('webpack');

// create plugins
const extractPlugin = new ExtractTextPlugin({
    filename: 'main.css'
});

module.exports = {
    entry: './assets/js/app.js',
    output: {
        path: path.resolve(__dirname, 'wallet/static/wallet'),
        filename: 'bundle.js',
        // publicPath: '/wallet/static/wallet'
    },
    module: {
        rules: [{
            test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
            use: [{
                loader: 'url-loader',
                options: {
                    name: '[name].[ext]',
                    outputPath: 'font/',
                    limit: 80000,
                }
            }]
        }, {
            test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
            loader: 'file-loader'
        }, {
            test: /\.js$/,
            use: [{
                loader: 'babel-loader',
                options: {
                    presets: ['es2015']
                }
            }]
        }, {
            test: /\.scss$/,
            use: extractPlugin.extract({
                use: ['css-loader', 'sass-loader']
            }),
            exclude: ['assets/theme/']
        }, {
            test: /\.(jpg|png)$/,
            use: [{
                loader: 'file-loader',
                options: {
                    name: '[name].[ext]',
                    outputPath: 'img/',
                }
            }]
        }
        ]
    },
    plugins: [
        new wepback.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            Materialize: 'materialize-css'
        }),
        extractPlugin,
        new CleanWebpackPlugin(['wallet/static/wallet']),
        new CopyWebpackPlugin([
            // copy all favicon data
            {
                from: 'assets/img/favicons',
                to: 'img/favicons'
            },
            // copy dependencies of theme
            {
                from: 'assets/theme',
                to: 'theme'
            },
        ])
    ]
};