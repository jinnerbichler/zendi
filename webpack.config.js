const path = require('path');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const wepback = require('webpack');
const extractPlugin = new ExtractTextPlugin({
    filename: 'main.css'
});

module.exports = {
    entry: './src/js/app.js',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'bundle.js',
        publicPath: '/wallet/static/wallet'
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                use: [
                    {
                        loader: 'babel-loader',
                        options: {
                            presets: ['es2015']
                        }
                    }
                ]
            },
            {
                test: /\.scss$/,
                use: extractPlugin.extract({
                    use: ['css-loader', 'sass-loader']
                })
            },
            {
                test: /\.html$/,
                use: ['html-loader']
            },
            {
                test: /\.(jpg|png)$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: '[name].[ext]',
                            outputPath: 'img/',
                            // publicPath: 'img/'
                        }
                    }
                ]
            }
        ]
    },
    plugins: [
        new wepback.ProvidePlugin({
            $: 'jquery',
        }),
        extractPlugin,
        new CleanWebpackPlugin(['dist']),
        new CopyWebpackPlugin([
            // copy all favicon data
            {
                from: 'src/img/favicons',
                to: 'img/favicons'
            },
            // copy dependencies of theme
            {
                from: 'src/theme',
                to: 'theme'
            },
        ])
    ]
};